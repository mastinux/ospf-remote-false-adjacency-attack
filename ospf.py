#!/usr/bin/env python

import sys
import os
import termcolor as T
import time
import datetime

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import lg, info, setLogLevel
from mininet.util import dumpNodeConnections, quietRun, moveIntf, waitListening
from mininet.cli import CLI
from mininet.node import Switch, OVSSwitch, Controller, RemoteController
from subprocess import Popen, PIPE, check_output
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser
from utils import log, log2

REMOTE_ATTACK = 1

POX = '%s/pox/pox.py' % os.environ[ 'HOME' ]

ROUTERS = 4
OSPF_CONVERGENCE_TIME = 60 # value get waiting for all hosts to reach web servers using ./reachability.sh
CAPTURING_WINDOW = 10 + 2 * 40 # waiting for 
# 10 s between 2.2.2.3 Hello p. and 2.2.2.2 Hello p.
# + 2 * <dead interval> timeout to observe R2 behavior

# dirty Hello p. sent by 2.2.2.2 for 40 s (<dead interval>)

SWITCH_NAME = 'switch'
LOCAL_ATTACKER_NAME = 'latk'
REMOTE_ATTACKER_NAME = 'ratk'

QUAGGA_STATE_DIR = '/var/run/quagga-1.2.4'

setLogLevel('info')
#setLogLevel('debug')

parser = ArgumentParser("Configure simple OSPF network in Mininet.")
parser.add_argument('--sleep', default=3, type=int)
args = parser.parse_args()


class Router(Switch):
	"""
	Defines a new router that is inside a network namespace so that the
	individual routing entries don't collide.
	"""
	ID = 0
	def __init__(self, name, **kwargs):
		kwargs['inNamespace'] = True
		Switch.__init__(self, name, **kwargs)
		Router.ID += 1
		self.switch_id = Router.ID

	@staticmethod
	def setup():
		return

	def start(self, controllers):
		pass

	def stop(self):
		self.deleteIntfs()

	def log(self, s, col="magenta"):
		print T.colored(s, col)


class SimpleTopo(Topo):
	def __init__(self):
		# Add default members to class.
		super(SimpleTopo, self ).__init__()

		num_routers = ROUTERS

		routers = []
		for i in xrange(num_routers):
			router = self.addSwitch('R%d' % (i+1))
			routers.append(router)

		hosts = []

		hostname = 'h5-1'
		host = self.addNode(hostname)
		hosts.append(host)

		hostname = 'h4-1'
		host = self.addNode(hostname)
		hosts.append(host)

		hostname = REMOTE_ATTACKER_NAME
		host = self.addNode(hostname)
		hosts.append(host)

		# adding switch5
		switch_name = SWITCH_NAME + '5'
		self.addSwitch(switch_name, cls=OVSSwitch)
		self.addLink(switch_name, 'R2')
		self.addLink(switch_name, 'h5-1')

		# adding switch1
		switch_name = SWITCH_NAME + '1'
		self.addSwitch(switch_name, cls=OVSSwitch)
		self.addLink(switch_name, 'R1')
		self.addLink(switch_name, 'R2')

		# adding links between routers
		self.addLink('R1', 'R3')

		# adding switch3
		switch_name = SWITCH_NAME + '3'
		self.addSwitch(switch_name, cls=OVSSwitch)
		self.addLink(switch_name, 'R3')
		self.addLink(switch_name, 'R4')
		self.addLink(switch_name, REMOTE_ATTACKER_NAME)

		# adding switch4
		switch_name = SWITCH_NAME + '4'
		self.addSwitch(switch_name, cls=OVSSwitch)
		self.addLink(switch_name, 'R4')
		self.addLink(switch_name, 'h4-1')

		hostname = LOCAL_ATTACKER_NAME
		host = self.addNode(hostname)
		hosts.append(host)

		switch_name = SWITCH_NAME + '1'
		self.addLink(switch_name, LOCAL_ATTACKER_NAME)

		return


def getIP(hostname):
	if hostname == REMOTE_ATTACKER_NAME:
		return '10.0.3.66/24'

	if hostname == LOCAL_ATTACKER_NAME:
		return '10.0.1.66/24'

	subnet, idx = hostname.replace('h', '').split('-')

	ip = '10.0.%s.%s/24' % (subnet, idx)

	return ip


def getGateway(hostname):
	if hostname == REMOTE_ATTACKER_NAME:
		return '10.0.3.1'

	if hostname == LOCAL_ATTACKER_NAME:
		return '10.0.1.1'

	subnet, idx = hostname.replace('h', '').split('-')

	gw = '10.0.%s.254' % (subnet)

	return gw


def startWebserver(net, hostname, text="Default web server"):
	host = net.getNodeByName(hostname)
	return host.popen("python webserver.py --text '%s'" % text, shell=True)


def startPOXHub():
	log("Starting POX RemoteController")
	os.system("python %s --verbose forwarding.hub > /tmp/hub.log 2>&1 &" % POX)

	log2("pox RemoteController to start", args.sleep, col='cyan')


def stopPOXHub():
	log("Stopping POX RemoteController")
	os.system('pgrep -f pox.py | xargs kill -9')


def launch_attack(attacker_host, atk_mac_address, r_mac_address):
	log("launching attack", 'red')

	iface = None

	for i in attacker_host.intfList():
		iface = i.name

	attacker_host.popen("python attack.py %s %s %s %s > /tmp/attack.log 2>&1" % (REMOTE_ATTACK, iface, atk_mac_address, r_mac_address), shell=True)
	os.system('lxterminal -e "/bin/bash -c \'tail -f /tmp/attack.log\'" > /dev/null 2>&1 &')

	# TODO remote attack
	# controlla dati inviati da ratk

	log("attack launched", 'red')
	log("check opened terminals", 'red')


def init_quagga_state_dir():
	if not os.path.exists(QUAGGA_STATE_DIR):
		os.makedirs(QUAGGA_STATE_DIR)

	os.system('chown mininet:mininet %s' % QUAGGA_STATE_DIR)

	return


def main():
	os.system("reset")

	os.system("rm -r logs/*stdout 2> /dev/null")
	os.system("rm -f /tmp/R*.log /tmp/ospf-R?.pid /tmp/zebra-R?.pid 2> /dev/null")
	os.system("rm -f /tmp/c0.log /tmp/hub.log 2> /dev/null")
	os.system("rm -r /tmp/R*-tcpdump.cap 2> /dev/null")
	os.system("rm -r /tmp/h*tcpdump.cap /tmp/atk*tcpdump.cap 2> /dev/null")

	os.system("mn -c > /dev/null 2>&1")

	os.system('pgrep zebra | xargs kill -9')
	os.system('pgrep ospfd | xargs kill -9')
	os.system('pgrep pox | xargs kill -9')
	os.system('pgrep -f webserver.py | xargs kill -9')

	init_quagga_state_dir()

	startPOXHub()

	net = Mininet(topo=SimpleTopo(), switch=Router)
	net.addController(name='poxController', controller=RemoteController, ip='127.0.0.1', port=6633)
	net.start()

	local_attacker_host = None
	remote_attacker_host = None

	# CONFIGURING HOSTS
	for host in net.hosts:
		host.cmd("ifconfig %s-eth0 %s" % (host.name, getIP(host.name)))
		host.cmd("route add default gw %s" % (getGateway(host.name)))
		host.cmd("tcpdump -i %s-eth0 -w /tmp/%s-tcpdump.cap not arp &" % (host.name, host.name))

		if host.name == LOCAL_ATTACKER_NAME:
			local_attacker_host = host
			continue
		elif host.name == REMOTE_ATTACKER_NAME:
			remote_attacker_host = host
			continue
		else:
			log("Starting web server on %s" % host.name, 'yellow')
			startWebserver(net, host.name, "Web server on %s" % host.name)

		if host.name == 'h4-1':
			host.cmd('ping 10.0.1.2 -i 10 2>&1> /tmp/h4-1-ping.log &')

	local_atk1_mac_address = local_attacker_host.MAC()
	remote_atk1_mac_address = remote_attacker_host.MAC()

	# CONFIGURING ROUTERS
	for router in net.switches:
		if SWITCH_NAME not in router.name:
			router.cmd("sysctl -w net.ipv4.ip_forward=1")
			router.waitOutput()

	log("Waiting %d seconds for sysctl changes to take effect..." % args.sleep, col='cyan')
	sleep(args.sleep)

	r1_eth1_mac_address = None
	r3_eth2_mac_address = None

	for router in net.switches:
		if SWITCH_NAME not in router.name:
			router.cmd("~/quagga-1.2.4/zebra/zebra -f conf/zebra-%s.conf -d -i /tmp/zebra-%s.pid > logs/%s-zebra-stdout 2>&1" % \
				(router.name, router.name, router.name))
			router.waitOutput()
			router.cmd("~/quagga-1.2.4/ospfd/ospfd -f conf/ospfd-%s.conf -d -i /tmp/ospf-%s.pid > logs/%s-ospfd-stdout 2>&1" % \
				(router.name, router.name, router.name), shell=True)
			router.waitOutput()
			log("Starting zebra and ospfd on %s" % router.name)

			router.cmd("tcpdump -i %s-eth1 -w /tmp/%s-eth1-tcpdump.cap not arp 2>&1 > /tmp/%s-eth1-tcpdump.log &" % \
				(router.name, router.name, router.name))
			router.cmd("tcpdump -i %s-eth2 -w /tmp/%s-eth2-tcpdump.cap not arp 2>&1 > /tmp/%s-eth2-tcpdump.log &" % \
				(router.name, router.name, router.name))

		if router.name == 'R1':
			for i in router.intfList():
				if i.name == 'R1-eth1':
					r1_eth1_mac_address = i.MAC()

		if router.name == 'R3':
			for i in router.intfList():
				if i.name == 'R3-eth2':
					r3_eth2_mac_address = i.MAC()

	#"""
	log("Waiting for OSPF convergence (estimated %s)..." % \
		((datetime.datetime.now()+datetime.timedelta(0,OSPF_CONVERGENCE_TIME)).strftime("%H:%M:%S")), 'cyan')
	sleep(OSPF_CONVERGENCE_TIME)
	#"""

	#"""
	if REMOTE_ATTACK != 1:
		launch_attack(local_attacker_host, local_atk1_mac_address, r1_eth1_mac_address)
	else:
		launch_attack(remote_attacker_host, local_atk1_mac_address, r3_eth2_mac_address)
	#"""
	
	#"""
	log("Collecting data for %s seconds (estimated %s)..." % \
		(CAPTURING_WINDOW, (datetime.datetime.now()+datetime.timedelta(0,CAPTURING_WINDOW)).strftime("%H:%M:%S")), 'cyan')
	sleep(CAPTURING_WINDOW)
	#"""
	
	#CLI(net)
	#raw_input('press ENTER to stop mininet...')

	net.stop()

	stopPOXHub()

	os.system('pgrep zebra | xargs kill -9')
	os.system('pgrep bgpd | xargs kill -9')
	os.system('pgrep pox | xargs kill -9')
	os.system('pgrep -f webserver.py | xargs kill -9')

	os.system('sudo wireshark /tmp/R2-eth2-tcpdump.cap -Y \'not ipv6\' &')

	if REMOTE_ATTACK != 1:
		os.system('sudo wireshark /tmp/latk-tcpdump.cap -Y \'not ipv6\' &')
	else:
		os.system('sudo wireshark /tmp/ratk-tcpdump.cap -Y \'not ipv6\' &')
		os.system('sudo wireshark /tmp/R3-eth1-tcpdump.cap -Y \'not ipv6\' &')


if __name__ == "__main__":
	main()
