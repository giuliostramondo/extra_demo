#/bin/bash

SCHEDULE_ANALYSIS_FILE=$1
INPUT_FILE_STEM=${SCHEDULE_ANALYSIS_FILE%.*}
best_cfg=`cat ${SCHEDULE_ANALYSIS_FILE} | tail -n +2 |sed "s/,/ /g" | sort -k9rn -k1n | head -n 1`
P=`echo $best_cfg | awk '{print $2}'`
Q=`echo $best_cfg | awk '{print $3}'`
SCHEME=`echo $best_cfg | awk '{print $4}'`
FREQUENCY=`echo $best_cfg | awk '{print $10}'`
SCHEDULE=`echo $best_cfg | awk '{print $11}'`
echo "P=\"$P\""> ./${INPUT_FILE_STEM}.cfg
echo "Q=\"$Q\"">> ./${INPUT_FILE_STEM}.cfg
echo "SCHEME=\"$SCHEME\"">> ./${INPUT_FILE_STEM}.cfg
echo "FREQUENCY=\"$FREQUENCY\"">> ./${INPUT_FILE_STEM}.cfg
echo "SCHEDULE=\"$(basename $SCHEDULE)\"">> ./${INPUT_FILE_STEM}.cfg
