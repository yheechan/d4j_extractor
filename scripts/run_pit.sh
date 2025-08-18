#!/bin/bash

set -e

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <PID> <BID> <EXPERIMENT-LABEL> <NUM_THREADS>"
    exit 1
fi

PID=$1
BID=$2
EXPERIMENT_LABEL=$3
NUM_THREADS=$4

pid_dir="/ssd_home/yangheechan/defects4j/${EXPERIMENT_LABEL}/${PID}"
out_dir="${pid_dir}/out_dir"
result_dir="$out_dir/$PID-${BID}b-result"
subjectInfo_dir="$result_dir/subjectInfo"

classes_relevant=$(cat "$subjectInfo_dir/classes_relevant-pit.txt")
test_relevant=$(cat "$subjectInfo_dir/test_relevant.txt")
dir_src_classes=$(cat "$subjectInfo_dir/dir_src_classes.txt")
dir_src_tests=$(cat "$subjectInfo_dir/dir_src_tests.txt")
dir_bin_classes=$(cat "$subjectInfo_dir/dir_bin_classes.txt")
dir_bin_tests=$(cat "$subjectInfo_dir/dir_bin_tests.txt")
cp_test=$(cat "$subjectInfo_dir/cp_test.txt")


# Enhanced classpath with JUnit 4
# PITEST_JAR="/home/yangheechan/.d4j_src/pitest/pitest-command-line/target/pitest-command-line-dev-SNAPSHOT.jar"
# enhanced_cp="/home/yangheechan/.d4j_src/defects4j/framework/projects/lib/junit-4.12-hamcrest-1.3.jar:$cp_test"
enhanced_cp="$JUNIT4_JAR:$cp_test"
PIT_REPORTER_CLASS="org.pitest.mutationtest.commandline.MutationCoverageReport"



# redirect the stderr and stdout to a log file
report_dir="$result_dir/pit-results"
mkdir -p "$report_dir"
log_file="$subjectInfo_dir/pit-exec.log"

cd "$pid_dir/$PID-${BID}b"

java -Xmx20g -Xms4g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -cp "$enhanced_cp:$PITEST_JAR" \
  $PIT_REPORTER_CLASS \
  --reportDir "$report_dir" \
  --targetClasses $classes_relevant \
  --targetTests $test_relevant \
  --excludedClasses "*Test*,*Tests*,*TestCase*,*testbed*" \
  --sourceDirs $dir_src_classes \
  --outputFormats=CSV \
  --fullMatrixResearchMode \
  --saveMutantBytecode \
  --mutators ALL \
  --mutationUnitSize 1 \
  --threads $NUM_THREADS \
  > "$log_file" 2>&1

# write to a text file of the command executed before
echo "java -Xmx20g -Xms4g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -cp \"$enhanced_cp:$PITEST_JAR\" $PIT_REPORTER_CLASS --reportDir $report_dir --targetClasses $src_classes --targetTests $test_classes --excludedClasses \"*Test*,*Tests*,*TestCase*,*testbed*\" --sourceDirs $src_dir --outputFormats=CSV --fullMatrixResearchMode --saveMutantBytecode --mutators ALL --mutationUnitSize 5 --threads $NUM_THREADS" > "$subjectInfo_dir/command_executed.txt"
