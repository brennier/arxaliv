#!/bin/sh
cd ~/reddit/r2
../scripts/saferun.sh /var/tmp/solr.pid paster run run.ini r2/lib/solrsearch.py -c "run_changed($1)"
