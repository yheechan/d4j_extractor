#!/bin/bash

set -e

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <PID> <BID> <NUM_THREADS> <SRC_CLASS>"
    exit 1
fi

PID=$1
BID=$2
NUM_THREADS=$3
src_class=$4


pid_dir="/ssd_home/yangheechan/defects4j/${PID}"
out_dir="${pid_dir}/out_dir"

result_dir="$out_dir/$PID-${BID}b-result"
subjectInfo_dir="$result_dir/subjectInfo"

test_classes=$(cat "$subjectInfo_dir/test_classes.txt")
src_dir=$(cat "$subjectInfo_dir/src_dir.txt")
cp_test=$(cat "$subjectInfo_dir/cp_test.txt")


# Enhanced classpath with JUnit 4
# PITEST_JAR="/home/yangheechan/.d4j_src/pitest/pitest-command-line/target/pitest-command-line-dev-SNAPSHOT.jar"
# PIT_REPORTER_CLASS="org.pitest.mutationtest.commandline.MutationCoverageReport"
# enhanced_cp="/home/yangheechan/.d4j_src/defects4j/framework/projects/lib/junit-4.12-hamcrest-1.3.jar:$cp_test"
enhanced_cp="$JUNIT4_JAR:$cp_test"


# redirect the stderr and stdout to a log file
report_dir="$out_dir/$PID-${BID}b-result/perFileReport/$src_class-report"
mkdir -p "$report_dir"

log_dir="$out_dir/$PID-${BID}b-result/perFileLog/$src_class-log"
mkdir -p "$log_dir"
log_file="$log_dir/expected-time-exec.log"

cd "$pid_dir/$PID-${BID}b"

java -Xmx20g -Xms4g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -cp "$enhanced_cp:$PITEST_JAR" \
  $PIT_REPORTER_CLASS \
  --reportDir "$report_dir" \
  --targetClasses $src_class \
  --targetTests $test_classes \
  --excludedClasses "*Test*,*Tests*,*TestCase*,*testbed*" \
  --sourceDirs $src_dir \
  --fullMatrixResearchMode \
  --mutators ALL \
  --mutationUnitSize 5 \
  --threads $NUM_THREADS \
  --measureExpectedTime \
  > "$log_file" 2>&1


# write to a text file of the command executed before

echo "java -Xmx20g -Xms4g -cp \"$cp_test:$PITEST_JAR\" $PIT_REPORTER_CLASS --reportDir $report_dir --targetClasses $src_classes --targetTests $test_classes --excludedClasses \"*Test*,*Tests*,*TestCase*,*testbed*\" --sourceDirs $src_dir --fullMatrixResearchMode --mutators ALL --threads $NUM_THREADS" > "$report_dir/command_executed.txt"

