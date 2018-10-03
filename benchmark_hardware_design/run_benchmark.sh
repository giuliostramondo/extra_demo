#!/bin/bash 

declare -A CFG_PARAM

IFS="="
while read -r name value
do
    if [ ! -z "$name" ]; then
        CFG_PARAM+=(["$name"]="${value//\"/}")
        echo "Content of $name is ${value//\"/}"
    fi
done <current_input_no_includes.cfg

schedule="${CFG_PARAM["SCHEDULE"]}"

if [ -e "c_source_benchmark_output.csv" ];then
    rm c_source_benchmark_output.csv
fi
for repetitions in {1..10000..200};do
    ./PolyMemStream_out_synth_benchmark/RunRules/DFE/binaries/PRFStream $schedule $repetitions >> benchmark.out
    ./c_source_benchmark $repetitions >> c_source_benchmark.out
done
