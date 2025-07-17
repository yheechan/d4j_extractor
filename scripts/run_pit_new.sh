#!/bin/bash

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <PID> <BID> <NUM_THREADS>"
    exit 1
fi

PID=$1
BID=$2
NUM_THREADS=$3


work_dir="/ssd_home/yangheechan/d4j_test/"
mkdir -p "$work_dir"

out_dir="/ssd_home/yangheechan/d4j_test/out_dir/"
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
echo "Test classpath: $cp_test"

# Enhanced classpath with JUnit 4
enhanced_cp="$JUNIT4_JAR:$cp_test"

src_classes=$(defects4j export -p classes.relevant | tr '\n' ',' | sed 's/,$//')
echo "Source classes: $src_classes"

test_classes=$(defects4j export -p tests.relevant | tr '\n' ',' | sed 's/,$//')
echo "Test classes: $test_classes"

src_dir=$(defects4j export -p dir.src.classes)
echo "Source directory: $src_dir"

pitest_jar="/home/yangheechan/.d4j_src/pitest/pitest-command-line/target/pitest-command-line-dev-SNAPSHOT.jar"
echo "PIT classpath: $pitest_jar"

java -cp "$enhanced_cp:$pitest_jar" \
  org.pitest.mutationtest.commandline.MutationCoverageReport \
  --reportDir "$out_dir/$PID-$BID-report" \
  --targetClasses $src_classes \
  --targetTests $test_classes \
  --excludedClasses "*Test*,*Tests*,*TestCase*,*testbed*" \
  --sourceDirs $src_dir \
  --fullMatrixResearchMode \
  --mutators ALL \
  --mutationUnitSize 10 \
  --threads $NUM_THREADS

# write to a text file of the command executed before
echo "Executed command:"
echo "java -cp \"$cp_test:$pitest_jar\" org.pitest.mutationtest.commandline.MutationCoverageReport --reportDir $out_dir/$PID-$BID-report --targetClasses $src_classes --targetTests $test_classes --excludedClasses \"*Test*,*Tests*,*TestCase*,*testbed*\" --sourceDirs $src_dir --fullMatrixResearchMode --mutators ALL --threads $NUM_THREADS --measureExpectedTime" > "$out_dir/$PID-$BID-report/command_executed.txt"

