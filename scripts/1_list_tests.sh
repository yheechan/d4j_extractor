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
dir_bin_tests=$(cat "$subjectInfo_dir/dir_bin_tests.txt")
cp_test=$(cat "$subjectInfo_dir/cp_test.txt")


repo_dir="$pid_dir/${PID}-${BID}b"
cd $repo_dir

core_dir="$repo_dir/core${CORE}"
mkdir -p "$core_dir"


java -cp "$GZOLTAR_CLI_JAR:$dir_bin_tests:$dir_bin_classes:$cp_test" \
  com.gzoltar.cli.Main listTestMethods \
  $dir_bin_tests \
  --outputFile $subjectInfo_dir/all_tests.txt
