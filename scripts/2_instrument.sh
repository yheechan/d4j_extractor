#!/bin/bash

set -e

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <PID> <BID> <EXPERIMENT-LABEL> <CORE>"
    exit 1
fi

PID=$1
BID=$2
EXPERIMENT_LABEL=$3
CORE=$4

pid_dir="/ssd_home/yangheechan/defects4j/${EXPERIMENT_LABEL}/${PID}"
out_dir="${pid_dir}/out_dir"
result_dir="$out_dir/$PID-${BID}b-result"
subjectInfo_dir="$result_dir/subjectInfo"

dir_bin_classes=$(cat "$subjectInfo_dir/dir_bin_classes.txt")
cp_test=$(cat "$subjectInfo_dir/cp_test.txt")

# replace text of dir_bin_classes (e.g., target/classes) in cp_test with "core${CORE}/working_classes"
cp_test=$(echo "$cp_test" | sed "s|$dir_bin_classes|core${CORE}/working_classes|g")
echo $cp_test

repo_dir="$pid_dir/${PID}-${BID}b"
core_dir="$repo_dir/core${CORE}"
cd $core_dir


working_classes_dir_name="working_classes"
working_classes_dir="$core_dir/${working_classes_dir_name}"
instrument_classes_dir_name="instrument_classes"
instrument_classes_dir="$core_dir/${instrument_classes_dir_name}"


# if working_classes_dir does not exist create it
if [ ! -d "$working_classes_dir" ]; then
  mkdir -p "$working_classes_dir"
  cp -r $repo_dir/$dir_bin_classes/* $working_classes_dir
fi


# if instrument_classes_dir exists remove it
if [ -d "$instrument_classes_dir" ]; then
  rm -rf "$instrument_classes_dir"
fi


java -cp "$GZOLTAR_CLI_JAR:$GZOLTAR_AGENT_JAR:$cp_test" \
  com.gzoltar.cli.Main instrument \
  $working_classes_dir_name \
  --outputDirectory $instrument_classes_dir_name

