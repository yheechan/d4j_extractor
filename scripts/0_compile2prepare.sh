#!/bin/bash

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <PID> <BID> <EXPERIMENT-LABEL>"
    exit 1
fi

PID=$1
BID=$2
EXPERIMENT_LABEL=$3


pid_dir="/ssd_home/yangheechan/defects4j/${EXPERIMENT_LABEL}/${PID}"
mkdir -p "$pid_dir"

out_dir="${pid_dir}/out_dir"
mkdir -p "$out_dir"

result_dir="$out_dir/$PID-${BID}b-result"
subjectInfo_dir="$result_dir/subjectInfo"
# perFileReport_dir="$result_dir/perFileReport"
# perFileLog_dir="$result_dir/perFileLog"
mkdir -p "$result_dir"
mkdir -p "$subjectInfo_dir"
# mkdir -p "$perFileReport_dir"
# mkdir -p "$perFileLog_dir"

cd "$pid_dir"

# Checkout
rm -rf "$PID-${BID}b"; defects4j checkout -p "$PID" -v "${BID}b" -w "$PID-${BID}b"
cd "$pid_dir/$PID-${BID}b"


classes_relevant=$(defects4j export -p classes.relevant | tr '\n' ':' | sed 's/:$//')
echo $classes_relevant > "$subjectInfo_dir/classes_relevant.txt"
classes_relevant=$(defects4j export -p classes.relevant | tr '\n' ',' | sed 's/,$//')
echo $classes_relevant > "$subjectInfo_dir/classes_relevant-pit.txt"

test_relevant=$(defects4j export -p tests.relevant | tr '\n' ',' | sed 's/,$//')
echo $test_relevant > "$subjectInfo_dir/test_relevant.txt"

dir_src_classes=$(defects4j export -p dir.src.classes)
echo $dir_src_classes > "$subjectInfo_dir/dir_src_classes.txt"

dir_src_tests=$(defects4j export -p dir.src.tests)
echo $dir_src_tests > "$subjectInfo_dir/dir_src_tests.txt"

dir_bin_classes=$(defects4j export -p dir.bin.classes)
echo $dir_bin_classes > "$subjectInfo_dir/dir_bin_classes.txt"

dir_bin_tests=$(defects4j export -p dir.bin.tests)
echo $dir_bin_tests > "$subjectInfo_dir/dir_bin_tests.txt"

cp_test=$(defects4j export -p cp.test)
echo $cp_test > "$subjectInfo_dir/cp_test.txt"

# Compile the project
defects4j compile
