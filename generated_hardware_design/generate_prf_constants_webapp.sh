#!/bin/bash


CONFIGURATION_FILE=$1
path_to_engine_src="./PolyMemStream_out/EngineCode/src/prfstream"
declare -A CFG_PARAM

IFS="="
while read -r name value
do
    if [ ! -z "$name" ]; then
        CFG_PARAM+=(["$name"]="${value//\"/}")
        echo "Content of $name is ${value//\"/}"
    fi  
done <${CONFIGURATION_FILE}

cat ${path_to_engine_src}/PRFConstants.maxj_template | sed "s/%SCHEME%/${CFG_PARAM["SCHEME"]}/" | sed "s/%Q%/${CFG_PARAM["Q"]}/" | sed "s/%P%/${CFG_PARAM["P"]}/" | sed "s/%F%/${CFG_PARAM["FREQUENCY"]}/"> ${path_to_engine_src}/PRFConstants.maxj
