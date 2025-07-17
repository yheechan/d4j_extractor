from lib.database import Database
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
        self.slack = Slack(
            slack_channel=self.os_copy.get("SLACK_CHANNEL"),
            slack_token=self.os_copy.get("SLACK_TOKEN"),
            bot_name="Extractor Engine",
        )

        self.db = Database(
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