#!/bin/bash


# Write a script that sends ../lib/saver_engine.py to the following in remote servers
# /ssd_home/yangheechan/defects4j/lib/saver_engine.py

# the list of servers can is in ~/.hosts/mbfl_servers

servers=($(cat ~/.hosts/mbfl_servers))

for server in "${servers[@]}"; do
    echo "Sending ../lib/saver_engine.py to $server:/ssd_home/yangheechan/defects4j/lib/saver_engine.py"
    scp ../lib/saver_engine.py "$server:/ssd_home/yangheechan/defects4j/lib/saver_engine.py"
    echo "Finished sending ../lib/saver_engine.py to $server:/ssd_home/yangheechan/defects4j/lib/saver_engine.py"
done