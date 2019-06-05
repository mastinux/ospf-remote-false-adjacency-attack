#!/bin/bash

lxterminal -e "/bin/bash -c 'echo \"origin h5-1 destination h4-1\"; ./curl.sh h5-1 h4-1'" &
lxterminal -e "/bin/bash -c 'echo \"origin h4-1 destination h5-1\"; ./curl.sh h4-1 h5-1'" &

lxterminal -e "/bin/bash -c 'echo \"origin atk1 destination h4-1\"; ./curl.sh atk1 h4-1'" &
lxterminal -e "/bin/bash -c 'echo \"origin atk1 destination h5-1\"; ./curl.sh atk1 h5-1'" &
