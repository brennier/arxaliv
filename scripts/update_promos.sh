#!/bin/bash

cd ~/reddit/r2
/usr/local/bin/paster run run-1slot.ini -c "from r2.lib import promote; promote.Run()"
