#!bin/bash

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <PID> <BID> <UNIQUE_NAME>"
    exit 1
fi

PID=$1
BID=$2
UNIQUE_NAME=$3

pid_dir="/ssd_home/yangheechan/defects4j/${PID}"
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


cp -r $dir_bin_classes/* $UNIQUE_NAME

java -cp "$GZOLTAR_CLI_JAR:$GZOLTAR_AGENT_JAR" \
  com.gzoltar.cli.Main instrument \
  $UNIQUE_NAME \
  --outputDirectory instr-$UNIQUE_NAME

java -cp "$GZOLTAR_CLI_JAR:$GZOLTAR_AGENT_JAR:instr-$UNIQUE_NAME:$dir_bin_tests:$cp_test" \
  com.gzoltar.cli.Main runTestMethods \
  --testMethods tests.txt \
  --collectCoverage \
  --offline