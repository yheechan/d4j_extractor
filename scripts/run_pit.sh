#!/bin/bash

# Test script to verify ASM shading fix
# This attempts to trigger the ASM version conflict that was happening before

set -e
PID="Closure"
BID="1"

work_dir="/tmp/d4j_test/"
mkdir -p "$work_dir"

cd "$work_dir"

D4J="$D4J_HOME/framework/bin/defects4j"

# Checkout
rm -rf "$PID-${BID}b"; "$D4J" checkout -p "$PID" -v "${BID}b" -w "$PID-${BID}b"
cd "$work_dir/$PID-${BID}b"

# Compile the project
"$D4J" compile

# Collect metadata
cd "$work_dir/$PID-${BID}b"

cp_test=$($D4J export -p cp.test)
echo "Test classpath: $cp_test"

# Add JUnit 4 JAR for better PIT compatibility
JUNIT4_JAR="/home/yangheechan/.d4j_src/defects4j/framework/projects/lib/junit-4.12-hamcrest-1.3.jar"

# Enhanced classpath with JUnit 4
enhanced_cp="$JUNIT4_JAR:$cp_test"

src_classes=$($D4J export -p classes.relevant | tr '\n' ',' | sed 's/,$//')
echo "Source classes: $src_classes"

test_classes=$($D4J export -p tests.relevant | tr '\n' ',' | sed 's/,$//')
echo "Test classes: $test_classes"

src_dir=$($D4J export -p dir.src.classes)
echo "Source directory: $src_dir"

pitest_jar="/home/yangheechan/.d4j_src/pitest/pitest-command-line/target/pitest-command-line-dev-SNAPSHOT.jar"
echo "PIT classpath: $pitest_jar"

java -cp "$enhanced_cp:$pitest_jar" \
  org.pitest.mutationtest.commandline.MutationCoverageReport \
  --reportDir pit-reports \
  --targetClasses $src_classes \
  --targetTests $test_classes \
  --excludedClasses "*Test*,*Tests*,*TestCase*,*testbed*" \
  --sourceDirs $src_dir \
  --fullMatrixResearchMode \
  --mutators ALL \
  --threads 2 \
  --measureExpectedTime \
  --verbose
  # --outputFormats CSV \

# write to a text file of the command executed before
echo "Executed command:"
echo "java -cp \"$cp_test:$pitest_jar\" org.pitest.mutationtest.commandline.MutationCoverageReport --reportDir pit-reports --targetClasses $src_classes --targetTests $test_classes --excludedClasses \"*Test*,*Tests*,*TestCase*,*testbed*\" --sourceDirs $src_dir --fullMatrixResearchMode --mutators ALL --threads 2 --measureExpectedTime --verbose" > "{$PID}-{$BID}b-command_executed.txt"



# echo ""
# echo "2. Checking if ASM classes are properly relocated..."
# jar -tf /home/yangheechan/.d4j_src/pitest/pitest-command-line/target/pitest-command-line-dev-SNAPSHOT.jar | grep -E "org/objectweb/asm|org/pitest/.*reloc.*asm" | head -10

# echo ""
# echo "=== Summary ==="
# echo "If PIT runs without VerifyError or LinkageError, the ASM shading fix is working!"
