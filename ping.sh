#!/bin/bash

node="h1-1"

sudo python run.py --node $node --cmd "ping -c 1 10.0.1.254"

sudo python run.py --node $node --cmd "ping -c 1 10.0.3.1"
sudo python run.py --node $node --cmd "ping -c 1 10.0.3.2"

sudo python run.py --node $node --cmd "ping -c 1 10.0.2.254"
sudo python run.py --node $node --cmd "ping -c 1 10.0.2.1"
