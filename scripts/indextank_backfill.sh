#!/bin/bash

cd ~/reddit/r2
/home/reddit/reddit/scripts/saferun.sh /tmp/indextank_backfill.pid nice /usr/local/bin/paster --plugin=r2 run run-1slot.ini ../scripts/indextank_backfill.py -c "run()"
