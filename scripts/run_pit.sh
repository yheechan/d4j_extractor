#!/bin/bash

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <PID> <BID> <NUM_THREADS>"
    exit 1
fi

PID=$1
BID=$2
NUM_THREADS=$3


work_dir="/ssd_home/yangheechan/defects4j/${PID}"
mkdir -p "$work_dir"

out_dir="${work_dir}/out_dir/"
mkdir -p "$out_dir"

cd "$work_dir"

# Checkout
rm -rf "$PID-${BID}b"; defects4j checkout -p "$PID" -v "${BID}b" -w "$PID-${BID}b"
cd "$work_dir/$PID-${BID}b"

# Compile the project
defects4j compile

# Collect metadata
cd "$work_dir/$PID-${BID}b"

cp_test=$(defects4j export -p cp.test)

# Enhanced classpath with JUnit 4
enhanced_cp="$JUNIT4_JAR:$cp_test"

src_classes=$(defects4j export -p classes.relevant | tr '\n' ',' | sed 's/,$//')
test_classes=$(defects4j export -p tests.relevant | tr '\n' ',' | sed 's/,$//')
src_dir=$(defects4j export -p dir.src.classes)

# redirect the stderr and stdout to a log file
report_dir="$out_dir/$PID-${BID}b-report"
mkdir -p "$report_dir"
log_file="$report_dir/log.txt"

java -cp "$enhanced_cp:$PITEST_JAR" \
  $PIT_REPORTER_CLASS \
  --reportDir "$report_dir" \
  --targetClasses $src_classes \
  --targetTests $test_classes \
  --excludedClasses "*Test*,*Tests*,*TestCase*,*testbed*" \
  --sourceDirs $src_dir \
  --fullMatrixResearchMode \
  --mutators ALL \
  --mutationUnitSize 10 \
  --threads $NUM_THREADS \
  > "$log_file" 2>&1

rm -rf "$work_dir/$PID-${BID}b"

# write to a text file of the command executed before

echo "java -cp \"$cp_test:$PITEST_JAR\" $PIT_REPORTER_CLASS --reportDir $report_dir --targetClasses $src_classes --targetTests $test_classes --excludedClasses \"*Test*,*Tests*,*TestCase*,*testbed*\" --sourceDirs $src_dir --fullMatrixResearchMode --mutators ALL --threads $NUM_THREADS --measureExpectedTime" > "$report_dir/command_executed.txt"

