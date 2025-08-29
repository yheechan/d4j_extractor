#!/bin/bash

set -e

if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <PID> <BID> <EXPERIMENT-LABEL> <CORE> <TARGET_TESTS>"
    exit 1
fi

PID=$1
BID=$2
EXPERIMENT_LABEL=$3
CORE=$4
TARGET_TESTS=$5

pid_dir="/ssd_home/yangheechan/defects4j/${EXPERIMENT_LABEL}/${PID}"
out_dir="${pid_dir}/out_dir"
result_dir="$out_dir/$PID-${BID}b-result"
subjectInfo_dir="$result_dir/subjectInfo"

dir_bin_classes=$(cat "$subjectInfo_dir/dir_bin_classes.txt")
dir_bin_tests=$(cat "$subjectInfo_dir/dir_bin_tests.txt")
cp_test=$(cat "$subjectInfo_dir/cp_test.txt")

# replace text of dir_bin_classes (e.g., target/classes) in cp_test with "core${CORE}/working_classes"
cp_test=$(echo "$cp_test" | sed "s|$dir_bin_classes|core${CORE}/working_classes|g")
# cp_test="$JUNIT4_JAR:$cp_test"

repo_dir="$pid_dir/${PID}-${BID}b"
core_dir="$repo_dir/core${CORE}"
cd $core_dir


working_classes_dir_name="working_classes"
working_classes_dir="$core_dir/${working_classes_dir_name}"
instrument_classes_dir_name="instrument_classes"
instrument_classes_dir="$core_dir/${instrument_classes_dir_name}"


dir_bin_tests_dir="${repo_dir}/${dir_bin_tests}"

# if gzoltar.ser exists remove it
if [ -f "$core_dir/gzoltar.ser" ]; then
  rm "$core_dir/gzoltar.ser"
fi

java -cp "$GZOLTAR_CLI_JAR:$GZOLTAR_AGENT_JAR:$instrument_classes_dir_name:$dir_bin_tests_dir:$cp_test" \
  com.gzoltar.cli.Main runTestMethods \
  --testMethods "${subjectInfo_dir}/${TARGET_TESTS}.txt" \
  --collectCoverage \
  --offline
