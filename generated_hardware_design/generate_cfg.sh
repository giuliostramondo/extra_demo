#/bin/bash

INPUT_FILE_STEM=$1
best_cfg=`cat ../schedules/${INPUT_FILE_STEM}.analysis | tail -n +2 |sed "s/,/ /g" | sort -k7rn -k1n | head -n 1`
P=`echo $best_cfg | awk '{print $2}'`
Q=`echo $best_cfg | awk '{print $3}'`
SCHEME=`echo $best_cfg | awk '{print $4}'`
SCHEDULE=`echo $best_cfg | awk '{print $10}'`
echo "P=\"$P\""> ./${INPUT_FILE_STEM}.cfg
echo "Q=\"$Q\"">> ./${INPUT_FILE_STEM}.cfg
echo "SCHEME=\"$SCHEME\"">> ./${INPUT_FILE_STEM}.cfg
echo "SCHEDULE=\"$(basename $SCHEDULE)\"">> ./${INPUT_FILE_STEM}.cfg
