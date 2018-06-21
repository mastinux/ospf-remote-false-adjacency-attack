#!/bin/bash

lxterminal -e "/bin/bash -c 'echo \"origin testhost1 destination h4-1\"; /home/mininet/ospf-remote-false-adjacency-attack/curl.sh testhost1 h4-1'" &
lxterminal -e "/bin/bash -c 'echo \"origin testhost1 destination h5-1\"; /home/mininet/ospf-remote-false-adjacency-attack/curl.sh testhost1 h5-1'" &
