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
        self.RESULT_DIR = f"{self.D4J_DIR}{self.PID}/out_dir/{self.PID}-{self.BID}b-result"

        self.PERFILEREPORT_DIR = f"{self.RESULT_DIR}/perFileReport"
        self.SUBJECTINFO_DIR = f"{self.RESULT_DIR}/subjectInfo"

    def run(self):
        self.USING_CLASSES = self.get_using_classes()
        self.save_fault()
        self.save_line_info()
        self.save_tc_info()
        self.save_mutation_info()
        self.zip_result_dir()
    
    def get_using_classes(self):
        using_src_classes_txt = os.path.join(self.SUBJECTINFO_DIR, "using_src_classes.txt")
        with open(using_src_classes_txt, "r") as f:
            using_src_classes = f.read().strip().split(",")
        return [src_class.strip() for src_class in using_src_classes]

    def save_fault(self):
        values = [self.PID, self.BID, self.EL]
        self.DB.insert(
            "d4j_fault_info",
            "project, bug_id, experiment_label",
            values
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
        LOGGER.info(f"Fault information saved for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL} with fault index {self.fault_idx}.")

    def save_line_info(self):
        unique_line_idx = -1
        self.lineInfo2lineIdx = {}
        self.class2lineInfo = {}

        for target_class in self.USING_CLASSES:
            if target_class not in self.class2lineInfo:
                self.class2lineInfo[target_class] = {}

            line_info_csv = os.path.join(self.PERFILEREPORT_DIR, f"{target_class}-report", "line_info.csv")
            with open(line_info_csv, 'r') as csvfile:
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

                    self.class2lineInfo[target_class][line_info] = {
                        "line_idx": line_id,
                        "file": code_filename,
                        "class": class_name,
                        "method": method_name,
                        "line_num": line_num
                    }

                    # save project_line_data for unique lines for DB
                    if line_info not in self.lineInfo2lineIdx:
                        unique_line_idx += 1
                        # Store the line information to LINEINFO2LINEIDX
                        self.lineInfo2lineIdx[line_info] = {
                            "line_idx": unique_line_idx,
                            "file": code_filename,
                            "class": class_name,
                            "method": method_name,
                            "line_num": line_num
                        }

                        # Save the line information to DB
                        values = [
                            self.fault_idx, unique_line_idx, code_filename, class_name, method_name, line_num
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

    def save_tc_info(self):
        unique_tc_idx = -1
        self.project_tcs_data = {}
        self.class2tcsInfo = {}
        failing_tcs_count = 0
        passing_tcs_count = 0

        for target_class in self.USING_CLASSES:
            if target_class not in self.class2tcsInfo:
                self.class2tcsInfo[target_class] = {}

            baseline_test_results_dir = os.path.join(self.PERFILEREPORT_DIR, f"{target_class}-report", "baselineTestResults")
            for result_file in os.listdir(baseline_test_results_dir):
                if not result_file.endswith(".json"):
                    continue
                result_path = os.path.join(baseline_test_results_dir, result_file)
                with open(result_path, 'r') as f:
                    tc_data = json.load(f)

                    # Get the test case information
                    tc_idx = tc_data["test_info"]["test_id"]
                    test_name = tc_data["test_info"]["test_name"]
                    result = 1 if tc_data["test_info"]["result"] == "FAIL" else 0
                    execution_time_ms = tc_data["test_info"]["execution_time_ms"]

                    bit_sequence_length = tc_data["coverage"]["bit_sequence_length"]
                    dest_line_bit_seq = tc_data["coverage"]["line_coverage_bit_sequence"]

                    exception_type = tc_data["exception"]["type"]
                    exception_msg = tc_data["exception"]["message"]
                    stacktrace = tc_data["exception"]["stack_trace"]

                    # Store the test case information in class2tcsInfo
                    if test_name not in self.class2tcsInfo[target_class]:
                        self.class2tcsInfo[target_class][test_name] = {
                            "tc_idx": tc_idx,
                            "result": result,
                        }

                    # Save the unique test case data
                    if test_name not in self.project_tcs_data:
                        unique_tc_idx += 1
                        built_bit_sequence_list = ["0"] * len(self.lineInfo2lineIdx)  # Initialize with zeros
                        self.update_line_cov_bit_sequence(
                            built_bit_sequence_list, dest_line_bit_seq, self.class2lineInfo[target_class]
                        )
                        self.project_tcs_data[test_name] = {
                            "tc_idx": unique_tc_idx,
                            "result": result,
                            "execution_time_ms": execution_time_ms,
                            "bit_sequence_length": len(built_bit_sequence_list),
                            "line_coverage_bit_sequence": built_bit_sequence_list,
                            "exception_type": exception_type,
                            "exception_msg": exception_msg,
                            "stacktrace": stacktrace
                        }
                        if result == 1:
                            failing_tcs_count += 1
                        else:
                            passing_tcs_count += 1
                    elif test_name in self.project_tcs_data:
                        if execution_time_ms > self.project_tcs_data[test_name]["execution_time_ms"]:
                            # Update the existing test case data with the new one if it has a longer execution time
                            self.project_tcs_data[test_name]["execution_time_ms"] = execution_time_ms
                        self.update_line_cov_bit_sequence(
                            self.project_tcs_data[test_name]["line_coverage_bit_sequence"],
                            dest_line_bit_seq,
                            self.class2lineInfo[target_class]
                        )

        # Save the test case information to the database
        for test_name, tc_data in self.project_tcs_data.items():
            cov_bit_seq = "".join(tc_data["line_coverage_bit_sequence"])
            values = [
                self.fault_idx, tc_data["tc_idx"], test_name, tc_data["result"],
                tc_data["execution_time_ms"], tc_data["bit_sequence_length"],
                cov_bit_seq, tc_data["exception_type"], tc_data["exception_msg"],
                tc_data["stacktrace"]
            ]
            LOGGER.debug(f"{test_name} - {tc_data['tc_idx']} - {tc_data['result']} - {tc_data['bit_sequence_length']}\n\t{cov_bit_seq}")
            self.DB.insert(
                "d4j_tc_info",
                "fault_idx, tc_idx, test_name, result, execution_time_ms, bit_sequence_length, line_coverage_bit_sequence, exception_type, exception_msg, stacktrace",
                values
            )

        LOGGER.info(f"Save {unique_tc_idx+1} tcs information for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")
        LOGGER.info(f"Total failing tcs: {failing_tcs_count}, passing tcs: {passing_tcs_count} for subject {self.PID}, bug ID {self.BID}, experiment label {self.EL}.")

    def update_mut_cov_bit_sequence(self, built_bit_sequence, src_bit_seq, classTcsInfo_data):
        for tc_name, tc_data in self.project_tcs_data.items():
            if tc_name in classTcsInfo_data:
                src_tc_idx = int(classTcsInfo_data[tc_name]["tc_idx"])
                dest_tc_idx = tc_data["tc_idx"]
                if src_bit_seq[src_tc_idx] == "1":
                    built_bit_sequence[dest_tc_idx] = "1"

    def save_mutation_info(self):
        unique_mutation_idx = -1

        for target_class in self.USING_CLASSES:
            result_csv = os.path.join(self.PERFILEREPORT_DIR, f"{target_class}-report", "full_mutation_matrix.csv")
            with open(result_csv, 'r') as csvfile:
                reader = csv.reader(csvfile)
                # skip the header
                next(reader, None)
                for row in reader:
                    # Assuming the CSV has columns: mutant_id,class,method,line,mutator,result_transition,exception_type_transition,exception_msg_transition,stacktrace_transition,status,num_tests_run
                    mutation_idx = row[0]
                    class_name = row[1]
                    method = row[2]
                    line = row[3]
                    mutator = row[4]
                    result_transition = row[5]
                    exception_type_transition = row[6]
                    exception_msg_transition = row[7]
                    stacktrace_transition = row[8]
                    status = row[9]
                    num_tests_run = row[10]

                    built_result_cov = ["0"] * len(self.project_tcs_data)  # Initialize with zeros
                    built_exc_type_cov = ["0"] * len(self.project_tcs_data)  # Initialize with zeros
                    built_exc_msg_cov = ["0"] * len(self.project_tcs_data)  # Initialize with zeros
                    built_stacktrace_cov = ["0"] * len(self.project_tcs_data)  # Initialize with zeros
                    self.update_mut_cov_bit_sequence(
                        built_result_cov, result_transition, self.class2tcsInfo[target_class]
                    )
                    self.update_mut_cov_bit_sequence(
                        built_exc_type_cov, exception_type_transition, self.class2tcsInfo[target_class]
                    )
                    self.update_mut_cov_bit_sequence(
                        built_exc_msg_cov, exception_msg_transition, self.class2tcsInfo[target_class]
                    )
                    self.update_mut_cov_bit_sequence(
                        built_stacktrace_cov, stacktrace_transition, self.class2tcsInfo[target_class]
                    )

                    # Save the mutation information
                    result_cov = "".join(built_result_cov)
                    exc_type_cov = "".join(built_exc_type_cov)
                    exc_msg_cov = "".join(built_exc_msg_cov)
                    stacktrace_cov = "".join(built_stacktrace_cov)

                    unique_mutation_idx += 1
                    values = [
                        self.fault_idx, unique_mutation_idx, class_name, method, line,
                        mutator, result_cov, exc_type_cov, exc_msg_cov, stacktrace_cov,
                        status, len(self.project_tcs_data)
                    ]

                    self.DB.insert(
                        "d4j_mutation_info",
                        "fault_idx, mutation_idx, class, method, line, mutator, result_transition, exception_type_transition, exception_msg_transition, stacktrace_transition, status, num_tests_run",
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
