import csv
import re
import os
import json
import logging

LOGGER = logging.getLogger(__name__)


def clean_line(line):
    """Remove null bytes and other problematic characters"""
    # Remove null bytes
    line = line.replace('\0', '')
    # Remove other control characters except newlines and tabs
    line = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', line)
    return line


def get_line_info(file_path):
    lineIdx2lineInfo = {}
    lineIdx = -1
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            
            try:
                # Split only on the first $ to separate package from class+method+line
                packageName, leftover = line.split("$", 1)
                # Split only on the first # to separate class from method+line
                className, leftover = leftover.split("#", 1)
                className = ".".join([packageName, className])
                # Split only on the last : to separate method from line number
                methodName, lineNum = leftover.rsplit(":", 1)
                lineNum = int(lineNum)

                lineIdx += 1
                lineIdx2lineInfo[lineIdx] = {
                    "className": className,
                    "methodName": methodName,
                    "lineNum": lineNum
                }
            except (ValueError, IndexError):
                # Skip lines that can't be parsed correctly
                continue
    return lineIdx2lineInfo

def parse_execption(msg):
    # e.g, java.lang.NumberFormatException: For input string: "80000000" at java.base/java.lang.NumberFormatException.forInputString(NumberFormatException.java:65) at java.base/java.lang.Integer.parseInt(Integer.java:652) at java.base/java.lang.Integer.valueOf(Integer.java:957) at java.base/java.lang.Integer.decode(Integer.java:1436) at org.apache.commons.lang3.math.NumberUtils.createInteger(NumberUtils.java:684) at org.apache.commons.lang3.math.NumberUtils.createNumber(NumberUtils.java:474) at org.apache.commons.lang3.math.NumberUtilsTest.TestLang747(NumberUtilsTest.java:256) at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method) at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) at java.base/java.lang.reflect.Method.invoke(Method.java:566) at org.junit.runners.model.FrameworkMethod$1.runReflectiveCall(FrameworkMethod.java:50) at org.junit.internal.runners.model.ReflectiveCallable.run(ReflectiveCallable.java:12) at org.junit.runners.model.FrameworkMethod.invokeExplosively(FrameworkMethod.java:47) at org.junit.internal.runners.statements.InvokeMethod.evaluate(InvokeMethod.java:17) at org.junit.runners.ParentRunner.runLeaf(ParentRunner.java:325) at org.junit.runners.BlockJUnit4ClassRunner.runChild(BlockJUnit4ClassRunner.java:78) at org.junit.runners.BlockJUnit4ClassRunner.runChild(BlockJUnit4ClassRunner.java:57) at org.junit.runners.ParentRunner$3.run(ParentRunner.java:290) at org.junit.runners.ParentRunner$1.schedule(ParentRunner.java:71) at org.junit.runners.ParentRunner.runChildren(ParentRunner.java:288) at org.junit.runners.ParentRunner.access$000(ParentRunner.java:58) at org.junit.runners.ParentRunner$2.evaluate(ParentRunner.java:268) at org.junit.runners.ParentRunner.run(ParentRunner.java:363) at org.junit.runner.JUnitCore.run(JUnitCore.java:137) at org.junit.runner.JUnitCore.run(JUnitCore.java:115) at com.gzoltar.internal.core.test.junit.JUnitTestTask.call(JUnitTestTask.java:67) at com.gzoltar.internal.core.test.junit.JUnitTestTask.call(JUnitTestTask.java:27) at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:264) at java.base/java.lang.Thread.run(Thread.java:829)
    # split into exception_type, exception_msg, stacktrace

    if msg == "":
        return "None", "None", "None"

    parts = msg.split(" at ")
    exception_type_msg = parts[0].split(": ", 1)
    exception_type = exception_type_msg[0].strip()
    exception_msg = exception_type_msg[1] if len(exception_type_msg) > 1 else ""
    stacktrace = parts[1:] if len(parts) > 1 else []
    stacktrace = "at " + " at ".join(stacktrace)
    return exception_type, exception_msg, stacktrace

def get_test_info(file_path):
    tcIdx2tcInfo = {}
    tcsResults = {
        "fail": [],
        "pass": []
    }

    # Check file size first to detect corrupted files
    if not os.path.exists(file_path):
        LOGGER.warning(f"File {file_path} does not exist.")
        return tcIdx2tcInfo, tcsResults
        
    if os.path.getsize(file_path) < 100:  # Arbitrary threshold for "empty/corrupt"
        LOGGER.warning(f"File {file_path} is too small, likely corrupted.")
        return tcIdx2tcInfo, tcsResults

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            # Read and clean the entire file content first
            content = file.read()
            cleaned_content = clean_line(content)
            
            # Split into lines and process each line
            lines = cleaned_content.split('\n')
            
            # Merge broken CSV lines (stacktraces that span multiple lines)
            merged_lines = []
            current_line = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this looks like a proper CSV start (has test name pattern)
                if ('#test' in line or 'Test#' in line or '.Test' in line or 'TestCase#' in line) and line.count(',') >= 3:
                    # This is likely a new test row, save previous if exists
                    if current_line:
                        merged_lines.append(current_line)
                    current_line = line
                else:
                    # This is likely a continuation of stacktrace from previous line
                    if current_line:
                        current_line += " " + line
                        
            # Don't forget the last line
            if current_line:
                merged_lines.append(current_line)

            newTcIdx = -1
            for line_num, line in enumerate(merged_lines, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                try:
                    # Parse each line manually since csv.reader might fail with special characters
                    reader = csv.reader([line])
                    row = next(reader)
                    
                    # Skip rows that are too short (likely header or corrupted)
                    if len(row) < 4:
                        if line_num == 1:  # Skip header
                            continue
                        print(f"Line {line_num}: Skipping short row: {row}")
                        continue
                        
                    # If row is too long, join extra columns as stacktrace
                    if len(row) > 4:
                        name, outcome, nanoSecs = row[:3]
                        stacktrace = ','.join(row[3:])
                    else:
                        name, outcome, nanoSecs, stacktrace = row
                    
                    # Skip header row
                    if name == "name" or ("#" not in name):
                        continue

                    className, testName = name.split("#")
                    result = 1 if outcome == "FAIL" else 0
                    tc_duration_ms = float(nanoSecs) / 1_000_000
                    exception_type, exception_msg, stacktrace_parsed = parse_execption(stacktrace)

                    newTcIdx += 1
                    tcIdx2tcInfo[newTcIdx] = {
                        "className": className,
                        "methodName": testName,
                        "result": result,
                        "duration_ms": tc_duration_ms,
                        "exception_type": exception_type,
                        "exception_msg": exception_msg,
                        "stacktrace": stacktrace_parsed
                    }
                    if result == 1:
                        tcsResults["fail"].append(newTcIdx)
                    else:
                        tcsResults["pass"].append(newTcIdx)
                        
                except csv.Error as e:
                    print(f"Line {line_num}: CSV parsing error: {e}, Line content: {line[:100]}...")
                    continue
                except ValueError as e:
                    print(f"Line {line_num}: Value parsing error: {e}, Line content: {line[:100]}...")
                    continue
                except Exception as e:
                    print(f"Line {line_num}: Unexpected error: {e}")
                    continue
                    
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

    return tcIdx2tcInfo, tcsResults
    
def get_test_cov(file_path, tcIdx2tcInfo):
    # e.g., 0 0 0 0 1 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 1 1 1 1 1 1 1 1 1 0 1 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -

    with open(file_path, 'r') as file:
        line = file.readlines()

        for tcIdx, tcInfo in tcIdx2tcInfo.items():
            # e.g., 0 0 1 +
            tcCovData = "".join(line[tcIdx].strip().split())
            bitSeqStr = tcCovData[:-1]  # remove the last '+' character
            covBitVal = int(bitSeqStr, 2)
            resChar = tcCovData[-1]  # get the last character of the bit sequence

            if resChar == "+":
                if tcInfo["result"] != 0:
                    LOGGER.debug(tcIdx)
                    LOGGER.debug(json.dumps(tcInfo, indent=2))
                assert tcInfo["result"] == 0, f"Test case {tcIdx} result mismatch: expected 0, got {tcInfo['result']}"
            else:
                if tcInfo["result"] != 1:
                    LOGGER.debug(tcIdx)
                    LOGGER.debug(json.dumps(tcInfo, indent=2))
                assert tcInfo["result"] == 1, f"Test case {tcIdx} result mismatch: expected 1, got {tcInfo['result']}"
            
            tcInfo["covBitVal"] = covBitVal

def get_tests_from_file(file_path):
    tests = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            testType, classMethod = row
            className = classMethod.split("#")[0]
            methodName = classMethod.split("#")[-1]
            tests.append({
                "testType": testType,
                "className": className,
                "methodName": methodName
            })
    return tests

def check_test_match(src_test, target_test):
    return (src_test["className"] == target_test["className"] and
            src_test["methodName"] == target_test["methodName"])

def get_mutant_info(file_path):
    mutantInfo = {}
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith("Class:"):
                className = line.split(":")[1].strip()
            elif line.startswith("Method:"):
                methodName = line.split(":")[1].strip()
            elif line.startswith("Line Number:"):
                lineNumber = int(line.split(":")[1].strip())
            elif line.startswith("Mutator:"):
                mutator = line.split(":")[1].strip()
    
    mutantInfo["className"] = className
    mutantInfo["methodName"] = methodName
    mutantInfo["lineNumber"] = lineNumber
    mutantInfo["mutator"] = mutator
    
    return mutantInfo