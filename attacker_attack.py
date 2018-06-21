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

eight_bit_space = [1L, 2L, 4L, 8L, 16L, 32L, 64L, 128L]

def print_long_line():
	print '#################################################################################'


def log(s, col="green"):
	print T.colored(s, col)


def send_hello_packet(srcIP, dstIP):
	ip_packet = IP(src=srcIP, dst=dstIP, ttl=TTL, proto=89)

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

	ospf_hello_packet = ip_packet/ospf_header/ospf_payload

	ospf_hello_packet.show()
	print_long_line()

	print 'sending hello message at %s' % (datetime.datetime.now().strftime("%H:%M:%S"))

	send(ospf_hello_packet)


def send_empty_dbd_messages(srcIP, dstIP, n, interval):
	ip_packet = IP(src=srcIP, dst=dstIP, ttl=TTL, proto=89)

	seqNum = randint(0, 2147483648)

	ospf_header = OSPF_Hdr(\
		src='2.2.2.3',\
		type=2)

	ospf_payload = OSPF_DBDesc(\
		dbdescr=7L,\
		options=2L)

	ospf_dbd_message_packet = ip_packet/ospf_header/ospf_payload

	ospf_dbd_message_packet.show()
	print_long_line()

	for i in xrange(0, n):
		print 'sending %d-th dbd message with seqNum %d at %s' % (i+1, seqNum + i, datetime.datetime.now().strftime("%H:%M:%S"))

		sleep(interval)

		ospf_dbd_message_packet.payload.payload.ddseq = seqNum + i

		send(ospf_dbd_message_packet)


def send_hello_messages(srcIP, dstIP, interval):
	ip_packet = IP(src=srcIP, dst=dstIP, ttl=TTL, proto=89)

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

	dbd_message_packet = ip_packet/ospf_header/ospf_payload

	dbd_message_packet.show()
	print_long_line()

	i = 0

	while True:
		print 'sending %d-th hello message at %s' % (i+1, datetime.datetime.now().strftime("%H:%M:%S"))

		sleep(interval)

		send(dbd_message_packet)


def main():
	#send_hello_packet(SOURCE_ADDRESS, HELLO_DESTINATION_ADDRESS)
	send_hello_packet(SOURCE_ADDRESS, DESTINATION_ADDRESS)

	send_empty_dbd_messages(SOURCE_ADDRESS, DESTINATION_ADDRESS, 10, 2)

	#send_hello_messages(SOURCE_ADDRESS, HELLO_DESTINATION_ADDRESS, 30)
	send_hello_messages(SOURCE_ADDRESS, DESTINATION_ADDRESS, 30)


if __name__ == "__main__":
	main()
