#!/bin/bash

cd ~/reddit/r2
/home/reddit/reddit/scripts/saferun.sh /tmp/updatereddits.pid nice /usr/local/bin/paster --plugin=r2 run run-1slot.ini r2/lib/sr_pops.py -c "run()"
