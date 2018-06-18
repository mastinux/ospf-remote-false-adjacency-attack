#!/bin/bash

lxterminal -e "/bin/bash -c 'echo \"origin h1-1 destination h2-1\"; /home/mininet/ospf-remote-false-adjacency-attack/curl.sh h5-1 h4-1'" &
lxterminal -e "/bin/bash -c 'echo \"origin h1-1 destination h2-1\"; /home/mininet/ospf-remote-false-adjacency-attack/curl.sh h4-1 h5-1'" &
