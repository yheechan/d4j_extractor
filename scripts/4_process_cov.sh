#!/bin/bash

set -e

if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <PID> <BID> <EXPERIMENT-LABEL> <CORE> <WORK_NAME>"
    exit 1
fi

PID=$1
BID=$2
EXPERIMENT_LABEL=$3
CORE=$4
WORK_NAME=$5

pid_dir="/ssd_home/yangheechan/defects4j/${EXPERIMENT_LABEL}/${PID}"
out_dir="${pid_dir}/out_dir"
result_dir="$out_dir/$PID-${BID}b-result"
subjectInfo_dir="$result_dir/subjectInfo"

classes_relevant=$(cat "$subjectInfo_dir/classes_relevant.txt")
test_relevant=$(cat "$subjectInfo_dir/test_relevant.txt")
dir_src_classes=$(cat "$subjectInfo_dir/dir_src_classes.txt")
dir_src_tests=$(cat "$subjectInfo_dir/dir_src_tests.txt")
dir_bin_classes=$(cat "$subjectInfo_dir/dir_bin_classes.txt")
dir_bin_tests=$(cat "$subjectInfo_dir/dir_bin_tests.txt")
cp_test=$(cat "$subjectInfo_dir/cp_test.txt")

repo_dir="$pid_dir/${PID}-${BID}b"
core_dir="$repo_dir/core${CORE}"
cd $core_dir


working_classes_dir_name="working_classes"
working_classes_dir="$core_dir/${working_classes_dir_name}"
instrument_classes_dir_name="instrument_classes"
instrument_classes_dir="$core_dir/${instrument_classes_dir_name}"


coverage_output_dir="$result_dir/coverage_results"
if [ ! -d "$coverage_output_dir" ]; then
  mkdir -p "$coverage_output_dir"
fi

work_cov_dir="$coverage_output_dir/$WORK_NAME"

# if work_cov_dir exists remove it
if [ -d "$work_cov_dir" ]; then
  rm -rf "$work_cov_dir"
fi

if [ -f "gzoltar.ser" ]; then
  java -cp "$GZOLTAR_CLI_JAR" \
    com.gzoltar.cli.Main faultLocalizationReport \
    --buildLocation $working_classes_dir \
    --granularity line \
    --includes $classes_relevant \
    --dataFile gzoltar.ser \
    --outputDirectory $work_cov_dir \
    --family sfl
else
  echo "[ERROR] No gzoltar.ser file found"
  exit 1
fi
