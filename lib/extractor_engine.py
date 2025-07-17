from lib.database import CRUD
from lib.slack import Slack

from utils.file_utils import *
from utils.general_utils import *
from utils.command_utils import *

import os
import concurrent.futures
import logging
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)

class ExtractorEngine:
    def __init__(self, subject, parallel=10):
        self.PID = subject
        self.parallel = parallel

        load_dotenv()
        self.os_copy = os.environ.copy()
        self.SLACK = Slack(
            slack_channel=self.os_copy.get("SLACK_CHANNEL"),
            slack_token=self.os_copy.get("SLACK_TOKEN"),
            bot_name="Extractor Engine",
        )

        self.DB = CRUD(
            host=self.os_copy.get("DB_HOST"),
            port=self.os_copy.get("DB_PORT"),
            user=self.os_copy.get("DB_USER"),
            password=self.os_copy.get("DB_PASSWORD"),
            database=self.os_copy.get("DB"),
            slack_channel=self.os_copy.get("SLACK_CHANNEL"),
            slack_token=self.os_copy.get("SLACK_TOKEN"),
        )

        self.LIB_DIR = os.path.dirname(os.path.abspath(__file__))
        self.CURR_ROOT_PATH = os.path.dirname(self.LIB_DIR)
        self.UTILS_DIR = self.CURR_ROOT_PATH + "/utils"
        self.SCRIPTS_DIR = self.CURR_ROOT_PATH + "/scripts"
        self.MAIN_SCRIPT = self.CURR_ROOT_PATH + "/main.py"

        self.SERVER_LIST = get_servers_list(self.os_copy.get("SERVER_LIST_FILE"))
        self.BID_LIST = get_active_bugs_list(self.PID, self.os_copy.get("D4J_HOME"))
        self.BIG_LIST = self.BID_LIST[:3]

        self.REMOTE_D4J_DIR = self.os_copy.get("SERVER_HOME") + f"defects4j/"
        self.REMOTE_WORK_DIR = self.os_copy.get("SERVER_HOME") + f"defects4j/{self.PID}"
        self.REMOTE_OUT_DIR = self.os_copy.get("SERVER_HOME") + f"defects4j/{self.PID}/out_dir"

    def run(self):
        self.prepare_for_testing()
        self.run_mutation_testing()

    def prepare_for_testing(self, batch_size=5):
        # 1. Initialize file system in remote servers in parallel batches
        def prepare_server(server):
            make_directory(self.REMOTE_WORK_DIR, server)

            send_file(self.SCRIPTS_DIR + "/run_pit.sh", self.REMOTE_D4J_DIR, server)
            chmod_file(self.REMOTE_D4J_DIR + "run_pit.sh", "777", server)

            send_directory(self.LIB_DIR, self.REMOTE_D4J_DIR, server)
            send_directory(self.UTILS_DIR, self.REMOTE_D4J_DIR, server)
            send_file(self.MAIN_SCRIPT, self.REMOTE_D4J_DIR, server)

            send_file(self.CURR_ROOT_PATH + "/.env", self.REMOTE_D4J_DIR, server)

        def prepare_database():
            if not self.DB.table_exists("d4j_fault_info"):
                columns = [
                    "fault_idx SERIAL PRIMARY KEY",
                    "project TEXT",
                    "bug_id INT",
                    "experiment_label TEXT",
                    "UNIQUE (project, bug_id, experiment_label)" # --ENSURE UNIQUE COMBINATION
                ]
                col_str = ", ".join(columns)
                self.DB.create_table("d4j_fault_info", col_str)
            
            if not self.DB.table_exists("d4j_tc_info"):
                columns = [
                    "fault_idx INT NOT NULL", # -- Foreign key to d4j_fault_info(fault_idx)
                    "tc_idx INT",
                    "json_data TEXT",
                    "FOREIGN KEY (fault_idx) REFERENCES d4j_fault_info(fault_idx) ON DELETE CASCADE ON UPDATE CASCADE", # -- Automatically delete tc_info rows when bug_info is deleted, Update changes in bug_info to tc_info
                ]
                col_str = ", ".join(columns)
                self.DB.create_table("d4j_tc_info", col_str)

                self.DB.create_index(
                    "d4j_tc_info",
                    "idx_d4j_tc_info_fault_idx",
                    "fault_idx"
                )
            
            if not self.DB.table_exists("d4j_line_info"):
                columns = [
                    "fault_idx INT NOT NULL", # -- Foreign key to d4j_fault_info(fault_idx)
                    "line_idx INT",
                    "file TEXT",
                    "line_info TEXT",
                    "FOREIGN KEY (fault_idx) REFERENCES d4j_fault_info(fault_idx) ON DELETE CASCADE ON UPDATE CASCADE", # -- Automatically delete line_info rows when bug_info is deleted, Update changes in bug_info to line_info
                ]
                col_str = ", ".join(columns)
                self.DB.create_table("d4j_line_info", col_str)
                self.DB.create_index(
                    "d4j_line_info",
                    "idx_d4j_line_info_fault_idx",
                    "fault_idx"
                )
            
            if not self.DB.table_exists("d4j_mutation_info"):
                columns = [
                    "fault_idx INT NOT NULL", # -- Foreign key to d4j_fault_info(fault_idx)
                    "mutation_idx INT",
                    "class TEXT",
                    "method TEXT",
                    "line INT",
                    "mutator TEXT",
                    "result_transition TEXT",
                    "exception_type_transition TEXT",
                    "exception_msg_transition TEXT",
                    "stacktrace_transition TEXT",
                    "num_tests_run INT",
                    "FOREIGN KEY (fault_idx) REFERENCES d4j_fault_info(fault_idx) ON DELETE CASCADE ON UPDATE CASCADE", # -- Automatically delete mutation_info rows when bug_info is deleted, Update changes in bug_info to mutation_info
                ]
                col_str = ", ".join(columns)
                self.DB.create_table("d4j_mutation_info", col_str)
                self.DB.create_index(
                    "d4j_mutation_info",
                    "idx_d4j_mutation_info_fault_idx",
                    "fault_idx"
                )

        servers = self.SERVER_LIST
        for i in range(0, len(servers), batch_size):
            batch = servers[i:i+batch_size]
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = [executor.submit(prepare_server, server) for server in batch]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        LOGGER.error(f"Error preparing server: {e}")
        
        prepare_database()
        self.DB.__del__()
    
    def run_mutation_testing(self, batch_size=5):
        # 2. Run run_pit.sh <PID> <BID> <parallel>
        # Distribute BIDs among servers, each server only takes its assigned BIDs sequentially
        def run_pit_on_bugs(server, bug_ids):
            for bug_id in bug_ids:
                LOGGER.info(f"Running PIT on {bug_id} on server {server}")
                command = f"source ~/.bashrc; cd {self.REMOTE_D4J_DIR} && bash run_pit.sh {self.PID} {bug_id} {self.parallel}"
                execute_command(command, server)

        servers = self.SERVER_LIST
        bid_list = self.BIG_LIST
        n_servers = len(servers)
        # Distribute BIDs as evenly as possible
        bid_chunks = [[] for _ in range(n_servers)]
        for idx, bid in enumerate(bid_list):
            bid_chunks[idx % n_servers].append(bid)

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_servers) as executor:
            futures = [executor.submit(run_pit_on_bugs, server, server_bids) for server, server_bids in zip(servers, bid_chunks)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    LOGGER.error(f"Error running PIT on bug: {e}")