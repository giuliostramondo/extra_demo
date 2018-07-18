#!/bin/bash

path_to_engine_src="./PolyMemStream_out/EngineCode/src/prfstream"
declare -A CFG_PARAM

IFS="="
while read -r name value
do
    if [ ! -z "$name" ]; then
        CFG_PARAM+=(["$name"]="${value//\"/}")
        echo "Content of $name is ${value//\"/}"
    fi  
done <current_input.cfg 

cat ${path_to_engine_src}/PRFConstants.maxj_template | sed "s/%SCHEME%/${CFG_PARAM["SCHEME"]}/" | sed "s/%Q%/${CFG_PARAM["Q"]}/" | sed "s/%P%/${CFG_PARAM["P"]}/" > ${path_to_engine_src}/PRFConstants.maxj
