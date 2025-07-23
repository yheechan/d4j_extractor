import json
import os
import logging
import math
import random
import pickle
from dotenv import load_dotenv

from utils.postprocessor_utils import *

LOGGER = logging.getLogger(__name__)
SUBJECTS = ["Lang"]

class PostProcessorEngine:
    def __init__(self, experiment_label, mutation_cnt_range=10, repeat_range=10):
        self.EL = experiment_label
        self.MR = mutation_cnt_range
        self.RR = repeat_range

        load_dotenv()
        self.os_copy = os.environ.copy()
        self.RESEARCH_DATA = self.os_copy.get("RESEARCH_DATA")
        self.EL_DIR = f"{self.RESEARCH_DATA}/{self.EL}"
        self.OUT_DIR = f"{self.EL_DIR}/postprocessed_dataset"
    
    def run(self):
        self.prepare_directory()
        self.process_dataset()

    def process_dataset(self):
        statement_data = {}
        faulty_statement_data = {}
        
        for rid in range(1, self.RR + 1):
            pp_data = {}
            # Set for test dataset
            pp_data["test_dataset"] = {"x": {}, "y": {}}
            
            # Over all subject, set dataset for both test and different methods
            for subject in SUBJECTS:
                rid_dir = f"{self.EL_DIR}/{subject}/experiment_raw_results/repeat_{rid}"
                if not os.path.exists(rid_dir):
                    LOGGER.warning(f"Directory {rid_dir} does not exist.")
                    raise FileNotFoundError(f"Directory {rid_dir} does not exist.")
            
                
                # For each fault (bid) in the subject
                for bid_pkl_file_name in os.listdir(rid_dir):
                    bid = int(bid_pkl_file_name.split("_")[0])
                    # if bid != 1: continue
                    full_fault_id = f"{subject}_{bid}"
                    bid_pkl_file = os.path.join(rid_dir, bid_pkl_file_name)

                    bid_data = normalize_data(bid_pkl_file, self.MR)

                    #  Set the test dataset
                    set_statement_info = False
                    if full_fault_id not in statement_data:
                        set_statement_info = True
                        statement_data[full_fault_id] = []
                        faulty_statement_data[full_fault_id] = []

                    set_dataset(
                        pp_data["test_dataset"], full_fault_id, bid_data,
                        statement_data=statement_data, 
                        faulty_statement_data=faulty_statement_data,
                        mtc=self.MR,
                        set_statement_info=set_statement_info
                    )

                    # Set for mutation_cnt methods
                    set_mutation_cnt_methods(pp_data, bid_data, full_fault_id, self.MR)
            
            # Divide dataset into test, train, validation set using proper 10-fold CV
            versions = list(pp_data["test_dataset"]["x"].keys())
            self.divide_dataset(pp_data, versions, rid)

        # Save the statement information
        self.save_stmt_info(statement_data, faulty_statement_data)

    def divide_dataset(self, pp_data, versions, rid, train_val_split=0.9):
        random.seed(888)
        random.shuffle(versions)
        total_versions = len(versions)
        LOGGER.info(f"Total versions: {total_versions}")
        
        # Calculate fold sizes for 10-fold CV
        base_fold_size = total_versions // 10
        extra_versions = total_versions % 10
        
        # Create fold sizes: some folds will have base_fold_size+1, others base_fold_size
        fold_sizes = [base_fold_size + (1 if i < extra_versions else 0) for i in range(10)]
        LOGGER.info(f"Fold sizes: {fold_sizes} (total: {sum(fold_sizes)})")
        
        # Create fold boundaries
        fold_boundaries = [0]
        for size in fold_sizes:
            fold_boundaries.append(fold_boundaries[-1] + size)

        for method_name, data in pp_data.items():
            LOGGER.info(f"Processing method: {method_name}")

            # For each k-fold group
            for group_index in range(10):
                # Get test versions for this fold
                start_idx = fold_boundaries[group_index]
                end_idx = fold_boundaries[group_index + 1]
                test_versions = versions[start_idx:end_idx]
                train_versions = [v for v in versions if v not in test_versions]

                LOGGER.info(f"\tGroup {group_index + 1}: {len(test_versions)} test versions, {len(train_versions)} train versions")

                # Collect training data from all training versions
                train_pos_x = []
                train_neg_x = []

                for version in train_versions:
                    if version not in data["x"] or version not in data["y"]:
                        LOGGER.warning(f"Version {version} not found in data for method {method_name}")
                        raise ValueError(f"Version {version} not found in data for method {method_name}")
                        
                    pos_indices = [i for i, y in enumerate(data["y"][version]) if y == 0]
                    neg_indices = [i for i, y in enumerate(data["y"][version]) if y == 1]
                    assert len(pos_indices) + len(neg_indices) == len(data["y"][version]), "Mismatch in indices and labels length"

                    # Set Training Dataset: 10 negative samples for each positive sample
                    for pos_index in pos_indices:
                        
                        # Sample 10 negative examples for this positive example
                        random.seed(888)
                        random.shuffle(neg_indices)
                        for neg_index in neg_indices[:min(10, len(neg_indices))]:
                            train_pos_x.append(data["x"][version][pos_index])
                            train_neg_x.append(data["x"][version][neg_index])
                
                # Create test dataset for this fold
                test_x = {}
                test_y = {}
                for version in test_versions:
                    if version in data["x"] and version in data["y"]:
                        test_x[version] = data["x"][version]
                        test_y[version] = data["y"][version]
                
                # Shuffle training data
                random.seed(888)
                random.shuffle(train_pos_x)
                random.seed(888)
                random.shuffle(train_neg_x)

                # Divide into train and validation sets
                val_split_pos = round(len(train_pos_x) * train_val_split)
                val_split_neg = round(len(train_neg_x) * train_val_split)
                
                val_pos_x = train_pos_x[val_split_pos:]
                val_neg_x = train_neg_x[val_split_neg:]

                train_pos_x = train_pos_x[:val_split_pos]
                train_neg_x = train_neg_x[:val_split_neg]
                
                LOGGER.info(f"\tGroup {group_index + 1}: Train pos: {len(train_pos_x)}, Train neg: {len(train_neg_x)}, Val pos: {len(val_pos_x)}, Val neg: {len(val_neg_x)}")
                
                # Set the dataset group directory
                if method_name == "test_dataset":
                    group_dir = f"{self.OUT_DIR}/repeat_{rid}/{method_name}/group_{group_index + 1}"
                else:
                    group_dir = f"{self.OUT_DIR}/repeat_{rid}/methods/{method_name}/group_{group_index + 1}"
                
                if not os.path.exists(group_dir):
                    os.makedirs(group_dir, exist_ok=True)

                # Make directories for train, val, and test
                train_dir = f"{group_dir}/train"
                val_dir = f"{group_dir}/val"
                test_dir = f"{group_dir}/test"
                
                for dir_path in [train_dir, val_dir, test_dir]:
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)

                # Save training data
                with open(os.path.join(train_dir, "x_pos.pkl"), 'wb') as f:
                    pickle.dump(train_pos_x, f)
                with open(os.path.join(train_dir, "x_neg.pkl"), 'wb') as f:
                    pickle.dump(train_neg_x, f)

                # Save validation data
                with open(os.path.join(val_dir, "x_pos.pkl"), 'wb') as f:
                    pickle.dump(val_pos_x, f)
                with open(os.path.join(val_dir, "x_neg.pkl"), 'wb') as f:
                    pickle.dump(val_neg_x, f)

                # Save test data
                with open(os.path.join(test_dir, "x.pkl"), 'wb') as f:
                    pickle.dump(test_x, f)
                with open(os.path.join(test_dir, "y.pkl"), 'wb') as f:
                    pickle.dump(test_y, f)            

    def save_stmt_info(self, statement_data, faulty_statement_data):
        """
        Save the statement information as pkl files.
        """
        statement_info_dir = f"{self.OUT_DIR}/statement_info"
        if not os.path.exists(statement_info_dir):
            os.makedirs(statement_info_dir, exist_ok=True)

        # Save statement data
        with open(os.path.join(statement_info_dir, "statements.pkl"), 'wb') as f:
            pickle.dump(statement_data, f)
        
        # Save faulty statement data
        with open(os.path.join(statement_info_dir, "faulty_statement_set.pkl"), 'wb') as f:
            pickle.dump(faulty_statement_data, f)

    def prepare_directory(self):
        if not os.path.exists(self.OUT_DIR):
            os.makedirs(self.OUT_DIR, exist_ok=True)
        
        statement_info_dir = f"{self.OUT_DIR}/statement_info"
        if not os.path.exists(statement_info_dir):
            os.makedirs(statement_info_dir, exist_ok=True)

        for rid in range(1, self.RR + 1):
            test_dir = f"{self.OUT_DIR}/repeat_{rid}/test_dataset"
            if not os.path.exists(test_dir):
                os.makedirs(test_dir, exist_ok=True)


            for mid in range(1, self.MR + 1):
                mid_dir = f"{self.OUT_DIR}/repeat_{rid}/methods/mutCnt_{mid}"
                if not os.path.exists(mid_dir):
                    os.makedirs(mid_dir, exist_ok=True)

