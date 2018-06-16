#!/bin/bash

lxterminal -e "/bin/bash -c 'echo \"origin h1-1 destination h2-1\"; /home/mininet/ospf-remote-false-adjacency-attack/curl.sh h1-1 h2-1'" &
