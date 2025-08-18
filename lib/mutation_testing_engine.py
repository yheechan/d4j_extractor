
from utils.mutation_testing_utils import *
from utils.data_read_utils import *
from utils.general_utils import *


import json
import time
import os
import subprocess as sp
import concurrent.futures
import queue
import shutil
from dotenv import load_dotenv
import logging

LOGGER = logging.getLogger(__name__)

class MutationTestingEngine:
    def __init__(self, pid, bid, experiment_label, parallel, timeMeasurement=False):
        self.PID = pid
        self.BID = bid
        self.EL = experiment_label
        self.PARALLEL = parallel
        self.TIME_MEASUREMENT = timeMeasurement

        load_dotenv()
        self.os_copy = os.environ.copy()

        self.LIB_DIR = os.path.dirname(os.path.abspath(__file__))
        self.CURR_ROOT_PATH = os.path.dirname(self.LIB_DIR)
        self.UTILS_DIR = self.CURR_ROOT_PATH + "/utils"
        self.SCRIPTS_DIR = self.CURR_ROOT_PATH + "/scripts"
        self.MAIN_SCRIPT = self.CURR_ROOT_PATH + "/main.py"

        self.D4J_DIR = self.os_copy.get("SERVER_HOME") + f"defects4j/"
        self.WORK_DIR = f"{self.D4J_DIR}{self.EL}/{self.PID}"
        self.REPO_DIR = f"{self.WORK_DIR}/{self.PID}-{self.BID}b"
        self.RESULT_DIR = f"{self.WORK_DIR}/out_dir/{self.PID}-{self.BID}b-result"


    def run(self):

        # 1. Test for baseline results
        startTime = time.time()
        time_info = self.execute_baseline_results()
        self.EXEC_DURATION_SECS = (time.time() - startTime) * 2.0

        # 2. Get baseline results
        baseline_results = self.get_results("baseline")

        # 3. Save relevant_tests (tests that executed lines excecuted by failing tests)
        relevant_tests_dict, numLinesByFails = self.save_relevant_tests(baseline_results)

        # 4. get tasks, mutants to test
        mutantIdx2mutantInfo = self.get_mutants()

        if self.TIME_MEASUREMENT:
            self.save_time_measurement_info(
                relevant_tests_dict, 
                mutantIdx2mutantInfo, 
                time_info,
                numLinesByFails
            )
            return 

        # Get target bin classes directory
        target_bin_classes = ""
        with open(self.RESULT_DIR + "/subjectInfo/dir_bin_classes.txt", 'r') as f:
            target_bin_classes = f.read().strip()
        self.BIN_CLASSES_DIRNAME = target_bin_classes
        self.target_bin_classes_dir = os.path.join(self.REPO_DIR, target_bin_classes)

        # 5. Prepare for mutation testing
        self.prepare_for_mutation_testing()

        # 6. start mutation testing
        self.start_mutation_testing(mutantIdx2mutantInfo)

    def save_time_measurement_info(self, relevant_tests_dict, mutantIdx2mutantInfo, time_info, numLinesByFails):
        relevant_test_total_time_ms = 0
        num_failing_tcs = 0
        num_passing_tcs = 0
        for test_id, test_info in relevant_tests_dict.items():
            relevant_test_total_time_ms += test_info["duration_ms"]
            if test_info["result"] == 1:
                num_failing_tcs += 1
            else:
                num_passing_tcs += 1

        overall_data = {
            "pid": self.PID,
            "bid": self.BID,
            "experiment_label": self.EL,
            **time_info,
            "num_of_failing_tests": num_failing_tcs,
            "num_of_passing_tests": num_passing_tcs,
            "num_of_relevant_tests": len(relevant_tests_dict),
            "relevant_test_total_time_ms": relevant_test_total_time_ms,
            "num_mutants": len(mutantIdx2mutantInfo),
            "num_lines_executed_by_fail_tcs": numLinesByFails
        }

        dest_file = os.path.join(self.RESULT_DIR + "/subjectInfo/time_measurement.json")
        with open(dest_file, 'w') as f:
            json.dump(overall_data, f)

    def execute_baseline_results(self):
        # list all tests
        list_all_tests(self.PID, self.BID, self.EL, 0, self.SCRIPTS_DIR)

        # instrument
        inst_start_time = time.time()
        instrument(self.PID, self.BID, self.EL, 0, "baseline", self.SCRIPTS_DIR)
        inst_duration_sec = time.time() - inst_start_time

        # execute
        exec_start_time = time.time()
        execute_with_coverage(self.PID, self.BID, self.EL, 0, "baseline", "all_tests", self.SCRIPTS_DIR)
        exec_duration_sec = time.time() - exec_start_time

        # process_cov
        process_start_time = time.time()
        process_cov(self.PID, self.BID, self.EL, 0, "baseline", self.SCRIPTS_DIR)
        process_duration_sec = time.time() - process_start_time

        return {
            "instr_duration_sec": inst_duration_sec,
            "exec_duration_sec": exec_duration_sec,
            "process_duration_sec": process_duration_sec
        }

    def get_results(self, work_name):
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

    def save_relevant_tests(self, baseline_results):
        # get lines executed by all failing tcs
        linesExecutedByFailTcsBitVal = getLinesExecutedByFailTcs(baseline_results)

        # get relevant tests
        relevant_tests = get_relevant_tests(baseline_results, linesExecutedByFailTcsBitVal)

        all_tests = get_tests_from_file(os.path.join(
            self.RESULT_DIR, f"subjectInfo/all_tests.txt"
        ))

        # filter only to relevant tests
        filtered_tests = []
        for srcTcInfo in all_tests:
            for tcIdx, tcInfo in relevant_tests.items():
                if check_test_match(srcTcInfo, tcInfo):
                    filtered_tests.append(srcTcInfo)

        # write to file
        relevant_tests_txt = os.path.join(
            self.RESULT_DIR, f"subjectInfo/relevant_tests.txt"
        )
        with open(relevant_tests_txt, 'w') as f:
            for test in filtered_tests:
                classType = test["testType"]
                className = test["className"]
                methodName = test["methodName"]
                f.write(f"{classType},{className}#{methodName}\n")
        
        linesExecutedByFailTcsBitStr = format(linesExecutedByFailTcsBitVal, f'0{len(baseline_results["lineIdx2lineInfo"])}b')
        numLinesByFails = linesExecutedByFailTcsBitStr.count("1")
        return relevant_tests, numLinesByFails

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

    def prepare_for_mutation_testing(self):
        for core in range(self.PARALLEL):
            self.reset_working_directory(core)

    def reset_working_directory(self, core):
        core_working_dir = os.path.join(self.REPO_DIR, f"core{core}")
        working_classes_dir = os.path.join(core_working_dir, "working_classes")
        if os.path.exists(working_classes_dir):
            shutil.rmtree(working_classes_dir)
        os.makedirs(working_classes_dir, exist_ok=True)

        shutil.copytree(self.target_bin_classes_dir, working_classes_dir, dirs_exist_ok=True)

    def start_mutation_testing(self, mutantIdx2mutantInfo):
        def replace_class(core, srcClassPath, tgtClassPath):
            """
            srcClassPath (name can differ to tgtClassPath)
            but copy overwrite tgtClassPath with srcClassPath
            """
            try:
                shutil.copy2(srcClassPath, tgtClassPath)
                LOGGER.debug(f"core{core} Replaced class {tgtClassPath} with {srcClassPath}")
            except Exception as e:
                LOGGER.error(f"core{core} Failed to replace class {tgtClassPath} with {srcClassPath}: {e}")

        def worker(task_queue, core):
            """Worker function that conducts mutation testing for a mutant from a shared queue"""
            coreDir = os.path.join(self.REPO_DIR, f"core{core}")
            working_classes_dir = os.path.join(coreDir, "working_classes")

            while True:
                try:
                    mutantIdx, mutantInfo = task_queue.get(timeout=1)
                    if mutantIdx is None:
                        break

                    LOGGER.info(f"Starting mutation testing for mutant {mutantIdx}")

                    # 0. set information
                    mutantClassFilePath = mutantInfo["classFilePath"]
                    className = mutantInfo["className"]
                    relClassPath = className.replace('.', '/') + ".class"

                    # 1. replace ogClass with mutantClass
                    tgtClassPath = os.path.join(working_classes_dir, relClassPath)
                    srcClassPath = mutantClassFilePath
                    replace_class(core, srcClassPath, tgtClassPath)

                    try:
                        # 2. instrument
                        instrument(self.PID, self.BID, self.EL, core, f"mutant_{mutantIdx}", self.SCRIPTS_DIR, srcClassPath)

                        # 3. execute
                        execute_with_coverage(self.PID, self.BID, self.EL, core, f"mutant_{mutantIdx}", "relevant_tests", self.SCRIPTS_DIR, srcClassPath, timeout=self.EXEC_DURATION_SECS)

                        # 5. process cov
                        process_cov(self.PID, self.BID, self.EL, core, f"mutant_{mutantIdx}", self.SCRIPTS_DIR, srcClassPath)

                    except sp.TimeoutExpired:
                        LOGGER.warning(f"Core {core}: Mutant {mutantIdx} timed out (likely infinite loop)")
                    except sp.CalledProcessError as e:
                        if e.returncode == 124:  # timeout exit code
                            LOGGER.warning(f"Core {core}: Mutant {mutantIdx} execution timed out")
                        else:
                            LOGGER.error(f"Core {core}: Mutant {mutantIdx} failed with exit code {e.returncode}")
                    except Exception as e:
                        LOGGER.error(f"Core {core}: Mutant {mutantIdx} failed: {type(e).__name__}: {str(e)}")
                    finally:
                        # 6. replace mutantClass to ogClass
                        tgtClassPath = os.path.join(working_classes_dir, relClassPath)
                        srcClassPath = os.path.join(self.REPO_DIR, self.BIN_CLASSES_DIRNAME, relClassPath)
                        replace_class(core, srcClassPath, tgtClassPath)
                        
                        task_queue.task_done()
                except queue.Empty:
                    break


        task_queue = queue.Queue()
        for mutantIdx, mutantInfo in mutantIdx2mutantInfo.items():
            task_queue.put((mutantIdx, mutantInfo))
            LOGGER.debug(f"Added mutant {mutantIdx}")

        # Start worker threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.PARALLEL) as executor:
            futures = [
                executor.submit(worker, task_queue, core) for core in range(self.PARALLEL)
            ]

            # Wait for all tasks to be completed
            task_queue.join()

            # Signal all workers to shut down by adding sentinel values
            for _ in range(self.PARALLEL):
                task_queue.put((None, None))
            
            # Wait for all workers to finish
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    LOGGER.error(f"Mutation testing failed: {e}")
