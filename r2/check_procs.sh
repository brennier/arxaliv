#!/bin/sh

cd /home/ri/reddit/r2
/usr/bin/paster run run.ini supervise_watcher.py -c "Alert(restart_list=['MEM'])"
