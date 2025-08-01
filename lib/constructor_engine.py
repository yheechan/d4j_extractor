from lib.database import CRUD
from utils.consructor_utils import *

import json
import os
import logging
import pickle
import time
import concurrent.futures
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)

class ConstructorEngine:
    def __init__(self, pid, experiment_label):
        self.PID = pid
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
        self.RESEARCH_DATA = self.os_copy.get("RESEARCH_DATA")
        self.OUT_DIR = f"{self.RESEARCH_DATA}/{self.EL}/{self.PID}/experiment_raw_results"
        if not os.path.exists(self.OUT_DIR):
            os.makedirs(self.OUT_DIR, exist_ok=True)

        curr_path = os.getcwd()
        exp_config_file = os.path.join(curr_path, ".experiment_config")
        with open(exp_config_file, 'r') as f:
            self.EXP_CONFIG = json.load(f)

    def run(self):
        # Get the lines in DB
        self.BID2FID = get_bid2fid(self.DB, self.PID, self.EL)
        # # FOR TESTING USE LETS USE ONLY ONE BUG
        self.BID2FID = {bid: fid for bid, fid in self.BID2FID.items() if bid == 1}

        # Prepare the database for saving ground truth
        self.prepare_database()

        self.save_ground_truth()
        self.write_suspiciousness_scores()

    def save_ground_truth(self):
        # Check if ground truth already exists
        result = self.DB.value_exists(
            "d4j_ground_truth_info",
            conditions={"pid": self.PID}
        )

        if result == True:
            LOGGER.info(f"Ground truth for project {self.PID} already exists.")
            return
        
        LOGGER.info(f"Saving ground truth for project {self.PID}.")

        # Insert ground truth data into the database
        d4j_ground_truth_dir = self.RESEARCH_DATA + f"/d4j_ground_truth"
        if not os.path.exists(d4j_ground_truth_dir):
            LOGGER.error(f"Defects4J ground truth directory {d4j_ground_truth_dir} does not exist.")
            return

        # Iterate through ground truth files
        gid_files = [file for file in os.listdir(d4j_ground_truth_dir) if file.startswith(self.PID)]
        gid_files.sort()
        LOGGER.info(f"Found {len(gid_files)} ground truth files for project {self.PID}.")

        for gid_file in gid_files:
            # Extract bug ID from the file name
            bid = int(gid_file.split('.')[0].split('-')[1])
            LOGGER.debug(f"Processing ground truth file {gid_file} for bug ID {bid}.")

            # Get the lines in DB
            lineIdx2lineData = get_lineIdx2lineData(self.DB, self.BID2FID, bid)

            with open(os.path.join(d4j_ground_truth_dir, gid_file), 'r') as file:
                lines = file.readlines()
                gid_cnt = 0
                for line in lines:
                    parts = line.strip().split('#')
                    if len(parts) > 0 and len(parts) <= 3:
                        file_name, line_num, description = parts[0], parts[1], parts[2]

                        if check_line_exists(lineIdx2lineData, file_name, line_num):
                            LOGGER.debug(f"\tLine exists: {file_name}:{line_num}")
                            gt_line_idx, gt_method = get_method(lineIdx2lineData, file_name, line_num)
                            LOGGER.debug(f"\tGround truth saved: {file_name}:{gt_method}:{line_num}")
                        else:
                            # if file_name:line_num doesn't exist in lines
                            # then add a ground truth as the nearest line
                            LOGGER.warning(f"\tLine does not exist: {file_name}:{line_num}. Adding nearest line.")
                            gt_line_idx, gt_data = get_nearest_line(lineIdx2lineData, file_name, line_num)
                            if gt_data:
                                file_name = gt_data['file']
                                gt_method = gt_data['method']
                                line_num = gt_data['line_num']
                                LOGGER.debug(f"\tGround truth saved (nearest): {file_name}:{gt_method}:{line_num}")
                            else:
                                LOGGER.error(f"\tNo nearest line found for {file_name}:{line_num}. Skipping ground truth.")
                                continue

                        exists = self.DB.value_exists(
                            "d4j_ground_truth_info",
                            conditions={
                                "pid": self.PID,
                                "bid": bid,
                                "file": file_name,
                                "method": gt_method,
                                "line": line_num,
                                "line_idx": gt_line_idx
                            }
                        )

                        # Check if ground truth already exists
                        if exists:
                            LOGGER.debug(f"Ground truth already exists: {self.PID}, {bid}, {gid_cnt}, {file_name}, {gt_method}, {line_num}")
                            continue

                        # Initiate a new ground truth id
                        gid_cnt += 1
                        LOGGER.debug(f"\tgid: {gid_cnt}")
                        
                        # Insert ground truth into the database
                        values = [self.PID, bid, gid_cnt, file_name, gt_method, line_num, gt_line_idx, description]
                        self.DB.insert(
                            "d4j_ground_truth_info",
                            "pid, bid, gid, file, method, line, line_idx, description",
                            values
                        )
                        LOGGER.info(f"Ground truth saved: {self.PID}, {bid}, {gid_cnt}, {file_name}, {gt_method}, {line_num}, {description}")

    def prepare_database(self):
        if not self.DB.table_exists("d4j_ground_truth_info"):
            columns = [
                "pid TEXT NOT NULL",
                "bid INT NOT NULL",
                "gid INT",
                "file TEXT",
                "method TEXT",
                "line INT",
                "line_idx INT",
                "description TEXT",
            ]
            col_str = ", ".join(columns)
            self.DB.create_table("d4j_ground_truth_info", col_str)

    def write_suspiciousness_scores(self):

        # repeat ID
        for rid in range(1, self.EXP_CONFIG["num_repeats"] + 1):
            rid_dir = f"{self.OUT_DIR}/repeat_{rid}"
            if not os.path.exists(rid_dir):
                os.makedirs(rid_dir, exist_ok=True)

            # Process bug IDs concurrently with batch size of 10
            bid_fid_pairs = list(self.BID2FID.items())
            batch_size = 50
            
            # Process in batches to control resource usage
            for i in range(0, len(bid_fid_pairs), batch_size):
                batch = bid_fid_pairs[i:i + batch_size]
                LOGGER.info(f"Processing batch {i//batch_size + 1} with {len(batch)} bug IDs: {[bid for bid, _ in batch]}")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                    # Submit all tasks in the batch
                    future_to_bid = {
                        executor.submit(self._process_single_bug, rid_dir, bid, fid): bid 
                        for bid, fid in batch
                    }
                    
                    # Collect results as they complete
                    completed_count = 0
                    failed_bids = []
                    
                    for future in concurrent.futures.as_completed(future_to_bid):
                        bid = future_to_bid[future]
                        try:
                            future.result()  # This will raise any exception that occurred
                            completed_count += 1
                            LOGGER.info(f"Successfully processed bug ID {bid} ({completed_count}/{len(batch)} completed in batch)")
                        except Exception as exc:
                            failed_bids.append(bid)
                            LOGGER.error(f"Bug ID {bid} generated an exception: {exc}")
                            # Continue processing other bugs instead of failing immediately
                    
                    # Report batch completion status
                    if failed_bids:
                        LOGGER.error(f"Batch {i//batch_size + 1} completed with {len(failed_bids)} failures: {failed_bids}")
                        # Re-raise the first exception to maintain original behavior
                        raise RuntimeError(f"Processing failed for bug IDs: {failed_bids}")
                    else:
                        LOGGER.info(f"Batch {i//batch_size + 1} completed successfully ({completed_count}/{len(batch)} bugs processed)")

    def _process_single_bug(self, rid_dir, bid, fid):
        """
        Process a single bug ID - separated for concurrent execution.
        
        :param rid_dir: Directory for the current repeat ID
        :param bid: Bug ID  
        :param fid: Fault index
        """
        start_time = time.time()
        LOGGER.info(f"Processing bug ID {bid} with fault index {fid}.")
        
        # Create a thread-local database connection for thread safety
        db_start = time.time()
        thread_db = CRUD(
            host=self.os_copy.get("DB_HOST"),
            port=self.os_copy.get("DB_PORT"),
            user=self.os_copy.get("DB_USER"),
            password=self.os_copy.get("DB_PASSWORD"),
            database=self.os_copy.get("DB"),
            slack_channel=self.os_copy.get("SLACK_CHANNEL"),
            slack_token=self.os_copy.get("SLACK_TOKEN"),
        )
        db_connection_time = time.time() - db_start
        LOGGER.debug(f"Bug ID {bid}: Database connection established in {db_connection_time:.2f}s")
        
        try:
            output_file = os.path.join(rid_dir, f"{bid}_lineIdx2lineData.pkl")

            if not os.path.exists(output_file):
                # Get the lines in DB using thread-local connection
                lineIdx2lineData = get_lineIdx2lineData(thread_db, self.BID2FID, bid)
            else:
                with open(output_file, "rb") as f:
                    lineIdx2lineData = pickle.load(f)

            # check if "fault_line" exists as key of first item of lineIdx2lineData
            first_key = next(iter(lineIdx2lineData))
            if 'fault_line' not in lineIdx2lineData[first_key]:
                # Assign Ground Truth using thread-local connection
                assign_groundtruth(thread_db, self.PID, bid, lineIdx2lineData)

            # Measure sbfl and mbfl scores using thread-local connection
            measure_scores(self.EXP_CONFIG, thread_db, fid, lineIdx2lineData)

            # Save the results to file as pickled JSON
            with open(output_file, "wb") as f:
                pickle.dump(lineIdx2lineData, f)
            
            total_time = time.time() - start_time
            LOGGER.debug(f"Saved results for bug ID {bid} to {output_file} (total time: {total_time:.2f}s)")
            
        finally:
            # Ensure database connection is properly closed
            try:
                if hasattr(thread_db, 'cursor') and thread_db.cursor:
                    thread_db.cursor.close()
                if hasattr(thread_db, 'db') and thread_db.db:
                    thread_db.db.close()
                LOGGER.debug(f"Bug ID {bid}: Database connection closed")
            except Exception as e:
                LOGGER.warning(f"Error closing database connection for bug ID {bid}: {e}")
