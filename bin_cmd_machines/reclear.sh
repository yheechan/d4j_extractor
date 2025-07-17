#!/bin/bash

set -x

while true
do
    parallel-ssh -h ~/.hosts/mbfl_servers -i "./clear.sh"
    sleep 60 # 600초 = 10분
done

