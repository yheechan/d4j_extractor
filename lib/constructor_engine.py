from lib.database import CRUD
from utils.consructor_utils import *

import json
import os
import logging
import pickle
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
        self.OUT_DIR = f"{self.RESEARCH_DATA}/{self.EL}/{self.PID}"
        if not os.path.exists(self.OUT_DIR):
            os.makedirs(self.OUT_DIR, exist_ok=True)

    def run(self):
        # Get the lines in DB
        self.BID2FID = get_bid2fid(self.DB, self.PID, self.EL)

        self.save_ground_truth()
        self.write_suspiciousness_scores()

    def save_ground_truth(self):
        # Prepare the database for saving ground truth
        self.prepare_database()
        
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
                                raise ValueError(f"No nearest line found for {file_name}:{line_num}. Skipping ground truth.")
                        
                        
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

        for bid, fid in self.BID2FID.items():
            LOGGER.info(f"Processing bug ID {bid} with fault index {fid}.")
            # Get the lines in DB
            lineIdx2lineData = get_lineIdx2lineData(self.DB, self.BID2FID, bid)

            # Assign Ground Truth
            assign_gt(self.DB, self.PID, bid, lineIdx2lineData)

            # Measure sbfl and mbfl scores
            measure_scores(self.DB, self.PID, bid, fid, lineIdx2lineData)

            write_ranks(lineIdx2lineData)

            # Save the results to file as pickled JSON
            with open(os.path.join(self.OUT_DIR, f"{bid}_lineIdx2lineData.pkl"), "wb") as f:
                pickle.dump(lineIdx2lineData, f)
