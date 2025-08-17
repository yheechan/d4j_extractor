from lib.database import CRUD
from utils.data_read_utils import *
from utils.general_utils import *

import csv
import json
import os
import logging
from dotenv import load_dotenv
import shutil

LOGGER = logging.getLogger(__name__)

class SaverEngine:
    def __init__(self, pid, bid, experiment_label):
        self.PID = pid
        self.BID = bid
        self.EL = experiment_label

        load_dotenv()
        self.os_copy = os.environ.copy()
        self.DB = CRUD(
            host=self.os_copy.get("DB_HOST"),
            port=self.os_copy.get("DB_PORT"),
            user=self.os_copy.get("DB_USER"),
            password=self.os_copy.get("DB_PASSWORD"),
            database=self.os_copy.get("DB"),
            slack_channel=self.os_copy.get("SLACK_CHANNEL"),
            slack_token=self.os_copy.get("SLACK_TOKEN"),
        )

        self.D4J_DIR = self.os_copy.get("SERVER_HOME") + f"defects4j/"
        self.WORK_DIR = f"{self.D4J_DIR}{self.EL}/{self.PID}"
        self.RESULT_DIR = f"{self.WORK_DIR}/out_dir/{self.PID}-{self.BID}b-result"

    def run(self):
        self.fault_idx = self.save_fault()

        self.tcName2tcIdx = self.getTcName2tcIdx()
        baseline_results = self.get_results("baseline")
        linesExecutedByFailTcsBitVal = getLinesExecutedByFailTcs(baseline_results)
        relevant_tests = get_relevant_tests(baseline_results, linesExecutedByFailTcsBitVal)
        relevant_lines = get_relevant_lines(baseline_results, linesExecutedByFailTcsBitVal)
        set_relevant_line_cov_bit(relevant_tests, relevant_lines, baseline_results)

        self.save_line_info(relevant_lines)
        self.save_tc_info(
            relevant_tests,
            len(baseline_results["lineIdx2lineInfo"]),
            len(relevant_lines)
        )


        mutantIdx2mutantInfo = self.get_mutants()
        self.process_mutant_results(relevant_tests, mutantIdx2mutantInfo, len(baseline_results["lineIdx2lineInfo"]))
        self.save_mutation_info(mutantIdx2mutantInfo)
        self.zip_result_dir()
    
    def save_fault(self):
        values = [self.PID, self.BID, self.EL]
        self.DB.insert(
            "d4j_fault_info",
            "project, bug_id, experiment_label",
            values
        )

        fault_idx = self.DB.read(
            "d4j_fault_info",
            columns="fault_idx",
            conditions={
                "project": self.PID,
                "bug_id": self.BID,
                "experiment_label": self.EL
            }
        )

        if not fault_idx:
            LOGGER.error(f"Failed to retrieve fault index for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")
            return
        LOGGER.info(f"Fault information saved for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL} with fault index {fault_idx[0][0]}.")
        return fault_idx[0][0]
    
    def getTcName2tcIdx(self):
        relevant_tests_txt = os.path.join(self.RESULT_DIR, "subjectInfo/relevant_tests.txt")
        tcName2tcIdx = {}
        tcIdx = -1
        with open(relevant_tests_txt, 'r') as f:
            lines = f.readlines()
            for line in lines:
                tcType, tcName = line.strip().split(",")
                assert tcName not in tcName2tcIdx
                tcIdx += 1
                tcName2tcIdx[tcName] = int(tcIdx)
        return tcName2tcIdx

    def get_results(self, work_name):
        LOGGER.debug(f"Getting results for work name: {work_name}")
        # Get the results for the specified work name
        lineIdx2lineInfo = get_line_info(os.path.join(
            self.RESULT_DIR, f"coverage_results/{work_name}/sfl/txt/spectra.csv"
        ))

        tcIdx2tcInfo, tcsResults = get_test_info(os.path.join(
            self.RESULT_DIR, f"coverage_results/{work_name}/sfl/txt/tests.csv"
        ))

        get_test_cov(os.path.join(
            self.RESULT_DIR, f"coverage_results/{work_name}/sfl/txt/matrix.txt"
        ), tcIdx2tcInfo)

        return {
            "lineIdx2lineInfo": lineIdx2lineInfo,
            "tcIdx2tcInfo": tcIdx2tcInfo,
            "tcsResults": tcsResults
        }

    def save_line_info(self, relevant_lines):
        unique_line_idx = -1

        for lineIdx, lineInfo in relevant_lines.items():
            unique_line_idx += 1
            className = lineInfo["className"]
            methodName = lineInfo["methodName"]
            lineNum = lineInfo["lineNum"]
            fileName = className.replace(".", "/") + ".java"

            values = [
                self.fault_idx, unique_line_idx, fileName, className, methodName, lineNum
            ]
            self.DB.insert(
                "d4j_line_info",
                "fault_idx, line_idx, file, class, method, line_num",
                values
            )
    
        LOGGER.info(f"Save {unique_line_idx+1} lines for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")
    
    def update_line_cov_bit_sequence(self, built_bit_sequence, src_bit_seq, classLineInfo_data):
        for line_info, line_data in self.lineInfo2lineIdx.items():
            if line_info in classLineInfo_data:
                src_line_idx = int(classLineInfo_data[line_info]["line_idx"])
                dest_line_idx = line_data["line_idx"]
                if src_bit_seq[src_line_idx] == "1":
                    built_bit_sequence[dest_line_idx] = "1"

    def save_tc_info(self, relevant_tests, fullCovLen, relCovLen):
        unique_tc_idx = -1
        failing_tcs_count = 0
        passing_tcs_count = 0

        for tcIdx, tcInfo in relevant_tests.items():
            unique_tc_idx += 1
            className = tcInfo["className"]
            methodName = tcInfo["methodName"]
            result = tcInfo["result"]
            duration_ms = tcInfo["duration_ms"]
            exception_type = tcInfo["exception_type"]
            exception_msg = tcInfo["exception_msg"]
            stacktrace = tcInfo["stacktrace"]
            fullCovBitVal = tcInfo["covBitVal"]
            fullCovBitStr = format(fullCovBitVal, f'0{fullCovLen}b')
            relCovBitVal = tcInfo["relCovBitVal"]
            relCovBitStr = format(relCovBitVal, f'0{relCovLen}b')
            testName = className + "." + methodName + "()"

            values = [
                self.fault_idx, unique_tc_idx, testName, result, duration_ms,
                len(relCovBitStr), relCovBitStr, len(fullCovBitStr), fullCovBitStr,
                exception_type, exception_msg, stacktrace
            ]
            columns = [
                "fault_idx", "tc_idx", "test_name", "result", "execution_time_ms",
                "bit_sequence_length", "line_coverage_bit_sequence",
                "full_bit_sequence_length", "full_line_coverage_bit_sequence",
                "exception_type", "exception_msg", "stacktrace"
            ]
            col_str = ", ".join(columns)
            self.DB.insert(
                "d4j_tc_info",
                col_str,
                values
            )

            if result == 1:
                failing_tcs_count += 1
            else:
                passing_tcs_count += 1

        LOGGER.info(f"Save {unique_tc_idx+1} tcs information for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")
        LOGGER.info(f"Total failing tcs: {failing_tcs_count}, passing tcs: {passing_tcs_count} for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")

    def get_mutants(self):
        mutants_dir = os.path.join(self.RESULT_DIR, "pit-results/mutants")
        # traverse through mutant files
        # there are trees of directories
        mutantIdx2mutantInfo = {}
        for root, dirs, files in os.walk(mutants_dir):
            for filename in files:
                if filename.endswith(".class"):
                    # get absolute filepath to file
                    mutantIdx = int(filename.strip().split("_")[0])
                    classFilePath = os.path.join(root, filename)
                    infoFilePath = os.path.join(root, filename.replace(".class", ".info"))
                    mutantInfo = get_mutant_info(infoFilePath)
                    mutantInfo["classFilePath"] = classFilePath
                    mutantIdx2mutantInfo[mutantIdx] = mutantInfo
        return mutantIdx2mutantInfo

    def process_mutant_results(self, relevant_tests, mutantIdx2mutantInfo, num_lines):
        coverage_results_dir = os.path.join(self.RESULT_DIR, "coverage_results")
        
        # Initialize all mutants with default transition results in case they don't have coverage data
        num_tests = len(self.tcName2tcIdx)
        default_bit_sequence = "0" * num_tests
        
        for mutantIdx in mutantIdx2mutantInfo:
            if "result_transition" not in mutantIdx2mutantInfo[mutantIdx]:
                mutantIdx2mutantInfo[mutantIdx].update({
                    "result_transition": default_bit_sequence,
                    "exception_type_transition": default_bit_sequence,
                    "exception_msg_transition": default_bit_sequence,
                    "stacktrace_transition": default_bit_sequence,
                    "f2p_cov_sim": [1.0] * num_tests,
                    "p2f_cov_sim": [1.0] * num_tests,
                    "f2f_cov_sim": [1.0] * num_tests,
                    "p2p_cov_sim": [1.0] * num_tests,
                })
        
        for dirName in os.listdir(coverage_results_dir):
            if not dirName.startswith("mutant"):
                continue

            mutantIdx = int(dirName.split("_")[-1])
            
            # Skip if this mutant is not in our expected list
            if mutantIdx not in mutantIdx2mutantInfo:
                LOGGER.warning(f"Found results for mutant {mutantIdx} but no mutant info available")
                continue

            try:
                mutantResults = self.get_results(dirName)
                
                # Check if we got valid results
                if not mutantResults["tcIdx2tcInfo"]:
                    LOGGER.warning(f"No test results found for mutant {mutantIdx}, skipping")
                    continue
                    
            except Exception as e:
                LOGGER.error(f"Failed to get results for mutant {mutantIdx}: {e}")
                continue

            transition_results = {
                "result_transition": "",
                "exception_type_transition": "",
                "exception_msg_transition": "",
                "stacktrace_transition": "",
                "f2p_cov_sim": [],
                "p2f_cov_sim": [],
                "f2f_cov_sim": [],
                "p2p_cov_sim": [],
            }

            reversedMutantTcName2TcIdxInfo = {
                f"{tcInfo['className']}#{tcInfo['methodName']}": {
                    "tcIdx": tcIdx,
                    "className": tcInfo["className"],
                    "methodName": tcInfo["methodName"],
                    "result": tcInfo["result"],
                    "exception_type": tcInfo["exception_type"],
                    "exception_msg": tcInfo["exception_msg"],
                    "stacktrace": tcInfo["stacktrace"],
                    "covBitVal": tcInfo["covBitVal"]
                } for tcIdx, tcInfo in mutantResults["tcIdx2tcInfo"].items()
            }
            reversedRelevantTcName2tcIdxInfo = {
                f"{tcInfo['className']}#{tcInfo['methodName']}": {
                    "tcIdx": tcIdx,
                    "className": tcInfo["className"],
                    "methodName": tcInfo["methodName"],
                    "result": tcInfo["result"],
                    "exception_type": tcInfo["exception_type"],
                    "exception_msg": tcInfo["exception_msg"],
                    "stacktrace": tcInfo["stacktrace"],
                    "covBitVal": tcInfo["covBitVal"]
                } for tcIdx, tcInfo in relevant_tests.items()
            }
            for classNameSharpMethodName, tcIdx in self.tcName2tcIdx.items():
                if classNameSharpMethodName not in reversedRelevantTcName2tcIdxInfo:
                    LOGGER.error(f"Test case {classNameSharpMethodName} not found in relevant tests for mutant {mutantIdx}.")
                    raise ValueError(f"Test case {classNameSharpMethodName} not found in relevant tests for mutant {mutantIdx}.")

                baselineTcInfo = reversedRelevantTcName2tcIdxInfo[classNameSharpMethodName]
                if classNameSharpMethodName in reversedMutantTcName2TcIdxInfo:
                    mutantTcInfo = reversedMutantTcName2TcIdxInfo[classNameSharpMethodName]
                    # LOGGER.debug(f"Processing mutant {mutantIdx} for test case {tcIdx}.")
                    # LOGGER.debug(f"Baseline TC Info: {baselineTcInfo}")
                    # LOGGER.debug(f"Mutant TC Info: {mutantTcInfo}")
                    assert baselineTcInfo["className"] == mutantTcInfo["className"]
                    assert baselineTcInfo["methodName"] == mutantTcInfo["methodName"]

                    resultBit = self.returnTransitionBit(baselineTcInfo["result"], mutantTcInfo["result"])
                    exceptionTypeBit = self.returnTransitionBit(baselineTcInfo["exception_type"], mutantTcInfo["exception_type"])
                    exceptionMsgBit = self.returnTransitionBit(baselineTcInfo["exception_msg"], mutantTcInfo["exception_msg"])
                    stacktraceBit = self.returnTransitionBit(baselineTcInfo["stacktrace"], mutantTcInfo["stacktrace"])
                    
                    transition_type, cov_sim = self.returnCovSim(baselineTcInfo, mutantTcInfo, num_lines)
                    transition_results[f"{transition_type}_cov_sim"].append(cov_sim)
                else:
                    resultBit = "0"
                    exceptionTypeBit = "0"
                    exceptionMsgBit = "0"
                    stacktraceBit = "0"

                    if baselineTcInfo["result"] == 1:
                        transition_results["f2f_cov_sim"].append(1.0)
                    elif baselineTcInfo["result"] == 0:
                        transition_results["p2p_cov_sim"].append(1.0)

                transition_results["result_transition"] += resultBit
                transition_results["exception_type_transition"] += exceptionTypeBit
                transition_results["exception_msg_transition"] += exceptionMsgBit
                transition_results["stacktrace_transition"] += stacktraceBit

            # add the processed information to mutantIdx2mutantInfo
            mutantIdx2mutantInfo[mutantIdx].update(transition_results)

            LOGGER.info(f"Processed results for mutant {mutantIdx} with {len(relevant_tests)}:{len(self.tcName2tcIdx)} relevant tests.")

    def returnTransitionBit(self, baselineResult, mutantResult):
        if baselineResult != mutantResult:
            return "1"
        elif baselineResult == mutantResult:
            return "0"

    def returnCovSim(self, baselineTcInfo, mutantTcInfo, num_lines):
        baselineResult = baselineTcInfo["result"]
        mutantResult = mutantTcInfo["result"]

        baselineCovBitVal = baselineTcInfo["covBitVal"]
        mutantCovBitVal = mutantTcInfo["covBitVal"]
        
        baselineCovBitStr = format(baselineCovBitVal, f'0{num_lines}b')
        mutantCovBitStr = format(mutantCovBitVal, f'0{num_lines}b')

        cosine_sim = cosine_similarity(baselineCovBitStr, mutantCovBitStr)
        if baselineResult == 1 and mutantResult == 0:
            return ("f2p", cosine_sim)
        elif baselineResult == 0 and mutantResult == 1:
            return ("p2f", cosine_sim)
        elif baselineResult == 1 and mutantResult == 1:
            return ("f2f", cosine_sim)
        elif baselineResult == 0 and mutantResult == 0:
            return ("p2p", cosine_sim)

    def save_mutation_info(self, mutantIdx2mutantInfo):
        unique_mutation_idx = -1
        for mutantIdx, mutantInfo in mutantIdx2mutantInfo.items():
            className = mutantInfo["className"]
            methodName = mutantInfo["methodName"]
            lineNumber = mutantInfo["lineNumber"]
            mutator = mutantInfo["mutator"]
            
            # All mutants should now have transition data (either real or default)
            numTestsRun = len(mutantInfo["result_transition"])
            result_transition = mutantInfo["result_transition"]
            exception_type_transition = mutantInfo["exception_type_transition"]
            exception_msg_transition = mutantInfo["exception_msg_transition"]
            stacktrace_transition = mutantInfo["stacktrace_transition"]
            f2p_cov_sim = mutantInfo["f2p_cov_sim"]
            p2f_cov_sim = mutantInfo["p2f_cov_sim"]
            f2f_cov_sim = mutantInfo["f2f_cov_sim"]
            p2p_cov_sim = mutantInfo["p2p_cov_sim"]

            unique_mutation_idx += 1
            values = [
                self.fault_idx, unique_mutation_idx, className, methodName, lineNumber, mutator,
                result_transition, exception_type_transition, exception_msg_transition, stacktrace_transition,
                f2p_cov_sim, p2f_cov_sim, f2f_cov_sim, p2p_cov_sim, numTestsRun
            ]
            columns = [
                "fault_idx", "mutation_idx", "class", "method", "line", "mutator",
                "result_transition", "exception_type_transition", "exception_msg_transition", "stacktrace_transition",
                "f2p_cov_sim", "p2f_cov_sim", "f2f_cov_sim", "p2p_cov_sim", "num_tests_run"
            ]
            col_str = ", ".join(columns)
            self.DB.insert(
                "d4j_mutation_info",
                col_str,
                values
            )

        LOGGER.info(f"Save {unique_mutation_idx+1} mutation info for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")

    def zip_result_dir(self):
        zip_file = f"{self.RESULT_DIR}.zip"
        if os.path.exists(zip_file):
            os.remove(zip_file)

        shutil.make_archive(self.RESULT_DIR, 'zip', self.RESULT_DIR)
        LOGGER.info(f"Output directory {self.RESULT_DIR} zipped to {zip_file}.")

        shutil.rmtree(self.RESULT_DIR, ignore_errors=True)
