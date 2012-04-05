#!/bin/bash

cd ~/reddit/r2
#/home/reddit/reddit/scripts/saferun.sh /tmp/updatereddits.pid nice /usr/local/bin/paster --plugin=r2 run run.ini r2/lib/sr_pops.py -c "run()"
/usr/local/bin/paster run run.ini r2/arxaliv/autoinsert.py -c 'run()'
#/usr/local/bin/paster --plugin=r2 run run.ini ../scripts/indextank_backfill.py -c 'run(sleep_time=0, cursor=100000)'
/usr/local/bin/paster run run.ini r2/lib/indextank.py -c 'run_changed(drain=True)'
