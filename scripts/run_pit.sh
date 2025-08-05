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

out_dir="${work_dir}/out_dir"
mkdir -p "$out_dir"

cd "$work_dir"

# Checkout
rm -rf "$PID-${BID}b"; defects4j checkout -p "$PID" -v "${BID}b" -w "$PID-${BID}b"
cd "$work_dir/$PID-${BID}b"

src_classes=$(defects4j export -p classes.relevant | tr '\n' ',' | sed 's/,$//')
test_classes=$(defects4j export -p tests.relevant | tr '\n' ',' | sed 's/,$//')
src_dir=$(defects4j export -p dir.src.classes)
cp_test=$(defects4j export -p cp.test)

# Compile the project
defects4j compile


# Enhanced classpath with JUnit 4
enhanced_cp="$JUNIT4_JAR:$cp_test"



# redirect the stderr and stdout to a log file
report_dir="$out_dir/$PID-${BID}b-report"
mkdir -p "$report_dir"
log_file="$report_dir/pit-exec.log"

java -Xmx32g -Xms8g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -cp "$enhanced_cp:$PITEST_JAR" \
  $PIT_REPORTER_CLASS \
  --reportDir "$report_dir" \
  --targetClasses $src_classes \
  --targetTests $test_classes \
  --excludedClasses "*Test*,*Tests*,*TestCase*,*testbed*" \
  --sourceDirs $src_dir \
  --fullMatrixResearchMode \
  --mutators ALL \
  --mutationUnitSize 5 \
  --threads $NUM_THREADS \
  > "$log_file" 2>&1

rm -rf "$work_dir/$PID-${BID}b"

# write to a text file of the command executed before

echo "java -cp \"$cp_test:$PITEST_JAR\" $PIT_REPORTER_CLASS --reportDir $report_dir --targetClasses $src_classes --targetTests $test_classes --excludedClasses \"*Test*,*Tests*,*TestCase*,*testbed*\" --sourceDirs $src_dir --fullMatrixResearchMode --mutators ALL --threads $NUM_THREADS" > "$report_dir/command_executed.txt"

