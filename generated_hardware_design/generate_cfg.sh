#/bin/bash

best_cfg=`cat ../schedules/current_input.analysis | tail -n +2 |sed "s/,/ /g" | sort -k7rn -k1n | head -n 1`
P=`echo $best_cfg | awk '{print $2}'`
Q=`echo $best_cfg | awk '{print $3}'`
SCHEME=`echo $best_cfg | awk '{print $4}'`
SCHEDULE=`echo $best_cfg | awk '{print $10}'`
echo "P=\"$P\""> ./current_input.cfg
echo "Q=\"$Q\"">> ./current_input.cfg
echo "SCHEME=\"$SCHEME\"">> ./current_input.cfg
echo "SCHEDULE=\"$SCHEDULE\"">> ./current_input.cfg
