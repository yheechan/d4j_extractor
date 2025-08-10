#!/bin/bash

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <PID> <BID>"
    exit 1
fi

PID=$1
BID=$2


pid_dir="/ssd_home/yangheechan/defects4j/${PID}"
mkdir -p "$pid_dir"

out_dir="${pid_dir}/out_dir"
mkdir -p "$out_dir"

result_dir="$out_dir/$PID-${BID}b-result"
subjectInfo_dir="$result_dir/subjectInfo"
perFileReport_dir="$result_dir/perFileReport"
perFileLog_dir="$result_dir/perFileLog"
mkdir -p "$result_dir"
mkdir -p "$subjectInfo_dir"
mkdir -p "$perFileReport_dir"
mkdir -p "$perFileLog_dir"

cd "$pid_dir"

# Checkout
rm -rf "$PID-${BID}b"; defects4j checkout -p "$PID" -v "${BID}b" -w "$PID-${BID}b"
cd "$pid_dir/$PID-${BID}b"


src_classes=$(defects4j export -p classes.relevant | tr '\n' ',' | sed 's/,$//')
echo $src_classes > "$subjectInfo_dir/src_classes.txt"

test_classes=$(defects4j export -p tests.relevant | tr '\n' ',' | sed 's/,$//')
echo $test_classes > "$subjectInfo_dir/test_classes.txt"

src_dir=$(defects4j export -p dir.src.classes)
echo $src_dir > "$subjectInfo_dir/src_dir.txt"

cp_test=$(defects4j export -p cp.test)
echo $cp_test > "$subjectInfo_dir/cp_test.txt"

# Compile the project
defects4j compile
