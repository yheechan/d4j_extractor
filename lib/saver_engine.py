from lib.database import CRUD

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
        self.WORK_DIR = f"{self.D4J_DIR}{self.PID}"
        self.OUT_DIR = f"{self.D4J_DIR}{self.PID}/out_dir/{self.PID}-{self.BID}b-report"

    def run(self):
        self.save_fault()
        self.save_tc_info()
        self.save_line_info()
        self.save_mutation_info()
        self.zip_out_dir()
    
    def save_fault(self):
        self.DB.insert(
            "d4j_fault_info",
            "project, bug_id, experiment_label",
            f"'{self.PID}', '{self.BID}', '{self.EL}'"
        )

        self.fault_idx = self.DB.read(
            "d4j_fault_info",
            columns="fault_idx",
            conditions={
                "project": self.PID,
                "bug_id": self.BID,
                "experiment_label": self.EL
            }
        )

        if not self.fault_idx:
            LOGGER.error(f"Failed to retrieve fault index for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")
            return
        self.fault_idx = self.fault_idx[0][0]
        LOGGER.info(f"Fault information saved for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")
    
    def save_tc_info(self):
        BASELINE_TEST_RESULTS_DIR = f"{self.OUT_DIR}/baselineTestResults"
        if not os.path.exists(BASELINE_TEST_RESULTS_DIR):
            LOGGER.warning(f"Baseline test results directory {BASELINE_TEST_RESULTS_DIR} does not exist.")
            return

        # Save test case information to the database
        for result_file in os.listdir(BASELINE_TEST_RESULTS_DIR):
            if result_file.endswith(".json"):
                # e.g., result_file = "0_test_results.json"
                file_idx = result_file.split("_")[0]
                result_path = os.path.join(BASELINE_TEST_RESULTS_DIR, result_file)
                with open(result_path, 'r') as f:
                    tc_data = json.load(f)

                    tc_idx = tc_data["test_info"]["test_id"]
                    test_name = tc_data["test_info"]["test_name"]
                    result = 1 if tc_data["test_info"]["result"] == "FAIL" else 0
                    execution_time_ms = tc_data["test_info"]["execution_time_ms"]

                    bit_sequence_length = tc_data["coverage"]["bit_sequence_length"]
                    line_coverage_bit_sequence = tc_data["coverage"]["line_coverage_bit_sequence"]

                    exception_type = tc_data["exception"]["type"]
                    exception_msg = tc_data["exception"]["message"]
                    stacktrace = tc_data["exception"]["stack_trace"]

                    self.DB.insert(
                        "d4j_tc_info",
                        "fault_idx, tc_idx, test_name, result, execution_time_ms, bit_sequence_length, line_coverage_bit_sequence, exception_type, exception_msg, stacktrace",
                        f"{self.fault_idx}, {tc_idx}, '{test_name}', {result}, {execution_time_ms}, {bit_sequence_length}, '{line_coverage_bit_sequence}', '{exception_type}', '{exception_msg}', '{stacktrace}'"
                    )

        LOGGER.info(f"Test case information saved for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")
    
    def save_line_info(self):
        LINE_INFO_CSV = f"{self.OUT_DIR}/line_info.csv"
        if not os.path.exists(LINE_INFO_CSV):
            LOGGER.warning(f"Line info CSV file {LINE_INFO_CSV} does not exist.")
            return
        
        # Save line information to the database
        with open(LINE_INFO_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile)
            # skip the header
            next(reader, None)
            for row in reader:
                # Assuming the CSV has columns: 'line_idx', 'file', 'line_info'
                line_id = row[0]
                code_filename = row[1]
                line_info = row[2]
                class_name = line_info.split("#")[0]
                method_name = line_info.split("#")[1].split(":")[0]
                line_num = line_info.split("#")[1].split(":")[1]


                self.DB.insert(
                    "d4j_line_info",
                    "fault_idx, line_idx, file, class, method, line_num",
                    f"{self.fault_idx}, {line_id}, '{code_filename}', '{class_name}', '{method_name}', {line_num}"
                )
    
        LOGGER.info(f"Data saved for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")

    def save_mutation_info(self):
        full_MUTATION_MATRIX_CSV = f"{self.OUT_DIR}/full_mutation_matrix.csv"
        if not os.path.exists(full_MUTATION_MATRIX_CSV):
            LOGGER.warning(f"Full mutation matrix CSV file {full_MUTATION_MATRIX_CSV} does not exist.")
            return
        
        # Save mutation information to the database
        with open(full_MUTATION_MATRIX_CSV, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            # skip the header
            next(reader, None)
            for row in reader:
                # Assuming the CSV has columns: mutant_id,class,method,line,mutator,result_transition,exception_type_transition,exception_msg_transition,stacktrace_transition,status,num_tests_run
                mutation_idx = row['mutant_id']
                class_name = row['class']
                method = row['method']
                line = row['line']
                mutator = row['mutator']
                result_transition = row['result_transition']
                exception_type_transition = row['exception_type_transition']
                exception_msg_transition = row['exception_msg_transition']
                stacktrace_transition = row['stacktrace_transition']
                num_tests_run = row['num_tests_run']

                self.DB.insert(
                    "d4j_mutation_info",
                    "fault_idx, mutation_idx, class, method, line, mutator, result_transition, exception_type_transition, exception_msg_transition, stacktrace_transition, num_tests_run",
                    f"{self.fault_idx}, {mutation_idx}, '{class_name}', '{method}', {line}, '{mutator}', '{result_transition}', '{exception_type_transition}', '{exception_msg_transition}', '{stacktrace_transition}', {num_tests_run}"
                )

        LOGGER.info(f"Data saved for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")

    def zip_out_dir(self):
        zip_file = f"{self.OUT_DIR}.zip"
        if os.path.exists(zip_file):
            os.remove(zip_file)
        
        shutil.make_archive(self.OUT_DIR, 'zip', self.OUT_DIR)
        LOGGER.info(f"Output directory {self.OUT_DIR} zipped to {zip_file}.")

        shutil.rmtree(self.OUT_DIR, ignore_errors=True)