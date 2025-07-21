from utils.sbfl_utils import *
from utils.mbfl_utils import *
from utils.rank_utils import add_sbfl_ranks, add_mbfl_ranks


import logging
import json
import random

LOGGER = logging.getLogger(__name__)

def get_bid2fid(DB, PID, EL):
        """
        Get the mapping of bug IDs to line numbers from the database.
        :param DB: Database connection object.
        :param PID: Project ID.
        :param EL: Experiment label.
        :return: Dictionary mapping bug IDs to fault indices. (e.g., {bug_id: fault_idx})
        """
        bid_list = DB.read(
            "d4j_fault_info",
            columns="fault_idx, bug_id",
            conditions={
                "project": PID,
                "experiment_label": EL
            }
        )
        if not bid_list:
            LOGGER.error(f"No bug IDs found for project {PID} with experiment label {EL}.")
            return {}

        bid3fid = {}
        for fault_idx, bug_id in bid_list:
            bid3fid[bug_id] = fault_idx

        LOGGER.info(f"Retrieved {len(bid3fid)} bug IDs for project {PID}.")
        return bid3fid

def get_lineIdx2lineData(DB, BID2FID, BID):
    """
    Get the mapping of line indices to line data for a specific bug ID.
    """
    if BID not in BID2FID:
        LOGGER.error(f"Bug ID {BID} not found in BID2FID mapping.")
        return {}

    fault_idx = BID2FID[BID]
    line_data_list = DB.read(
        "d4j_line_info",
        columns="line_idx, file, class, method, line_num",
        conditions={"fault_idx": fault_idx}
    )

    lineIdx2lineData = {}
    for line_idx, file, class_name, method, line_num in line_data_list:
        lineIdx2lineData[line_idx] = {
            "file": file,
            "class": class_name,
            "method": method,
            "line_num": line_num
        }

    LOGGER.info(f"Retrieved {len(lineIdx2lineData)} lines for bug ID {BID}.")
    return lineIdx2lineData

def check_line_exists(lineIdx2lineData, file_name, line_num):
        """
        Check if the line exists in the lineIdx2lineData mapping.
        """
        for line_idx, line_data in lineIdx2lineData.items():
            if line_data['file'] == file_name and line_data['line_num'] == int(line_num):
                return True
        return False

def get_method(lineIdx2lineData, file_name, line_num):
    """
    Get the method name for a specific file and line number.
    """
    for line_idx, line_data in lineIdx2lineData.items():
        if line_data['file'] == file_name and line_data['line_num'] == int(line_num):
            return (line_idx, line_data['method'])
    return None

def get_nearest_line(lineIdx2lineData, file_name, line_num):
    """
    Find the nearest line in the lineIdx2lineData mapping based on line number.
    This function should implement logic to find the closest line based on some criteria.
    """
    nearest_line = None
    min_distance = float('inf')

    for line_idx, line_data in lineIdx2lineData.items():
        if line_data['file'] == file_name:
            distance = abs(line_data['line_num'] - int(line_num))
            if distance < min_distance:
                min_distance = distance
                nearest_line = (line_idx, line_data)

    if nearest_line:
        LOGGER.info(f"Found nearest line for {file_name}:{line_num} - {nearest_line[1]['line_num']}")
    else:
        LOGGER.warning(f"No nearest line found for {file_name}:{line_num}.")

    return nearest_line

def assign_gt(DB, PID, BID, lineIdx2lineData):
    """
    Assign ground truth based on the line data and insert it into the database.
    :param DB: Database connection object.
    :param PID: Project ID.
    :param BID: Bug ID.
    :param lineIdx2lineData: Mapping of line indices to line data.
    """
    gd_list = DB.read(
        "d4j_ground_truth_info",
        columns="file, method, line, line_idx",
        conditions={"pid": PID, "bid": BID}
    )

    for file_name, method, line_num, line_idx in gd_list:
        lineIdx2lineData[line_idx]["fault_line"] = 1

    for lineIdx in lineIdx2lineData:
        if "fault_line" not in lineIdx2lineData[lineIdx].keys():
            lineIdx2lineData[lineIdx]['fault_line'] = 0

def get_tcIdx2tcInfo(DB, FID):
    """
    Get test case information for a specific fault index.
    :param DB: Database connection object.
    :param FID: Fault index.
    :return: List of test case information.
    """
    col = [
        "tc_idx", "test_name", "result", "execution_time_ms",
        "bit_sequence_length", "line_coverage_bit_sequence"
    ]
    col_str = ", ".join(col)
    tc_info = DB.read(
        "d4j_tc_info",
        columns=col_str,
        conditions={"fault_idx": FID}
    )

    tcIdx2tcInfo = {}
    for tc_data in tc_info:
        tc_idx, test_name, result, \
            execution_time_ms, bit_sequence_length, \
            line_coverage_bit_sequence = tc_data
        
        tcIdx2tcInfo[tc_idx] = {
            "test_name": test_name,
            "result": result,
            "execution_time_ms": execution_time_ms,
            "bit_sequence_length": bit_sequence_length,
            "line_coverage_bit_sequence": line_coverage_bit_sequence
        }

    return tcIdx2tcInfo

def get_lineIdx2mutation(DB, FID, lineIdx2lineData):
    """
    Get mutation information for a specific fault index.
    :param DB: Database connection object.
    :param FID: Fault index.
    :return: List of mutation information.
    """
    col = [
        "mutation_idx", "class", "method", "line",
        "result_transition", "exception_type_transition",
        "exception_msg_transition", "stacktrace_transition",
        "status", "num_tests_run"
    ]
    col_str = ", ".join(col)
    mutation_info = DB.read(
        "d4j_mutation_info",
        columns=col_str,
        conditions={"fault_idx": FID}
    )

    lineIdx2mutation = {}
    for lineIdx, line_data in lineIdx2lineData.items():
        lineIdx2mutation[lineIdx] = []
        line_class = line_data['class']
        line_method = line_data['method']
        line_num = line_data['line_num']

        for mutation in mutation_info:
            mutation_idx, class_name, method, line, \
                result_transition, exception_type_transition, \
                exception_msg_transition, stacktrace_transition, \
                status, num_tests_run = mutation
            
            if (class_name == line_class) \
                and (method in line_method) \
                and (line == line_num):
                mutation_data = {
                    "mutation_idx": mutation_idx,
                    "result_transition": result_transition,
                    "exception_type_transition": exception_type_transition,
                    "exception_msg_transition": exception_msg_transition,
                    "stacktrace_transition": stacktrace_transition,
                    "status": status,
                    "num_tests_run": num_tests_run
                }
                lineIdx2mutation[lineIdx].append(mutation_data)

    # shuffle the mutation list for each line
    for line_idx, mutation_list in lineIdx2mutation.items():
        if mutation_list:
            random.shuffle(mutation_list)
        else:
            LOGGER.warning(f"No mutations found for line index {line_idx}.")

    return lineIdx2mutation

def get_total_failing_tcs(tcIdx2tcInfo):
    """
    Get the total number of failing test cases.
    :param tcIdx2tcInfo: Mapping of test case indices to test case information.
    :return: Total number of failing test cases.
    """
    total_failing_tcs = sum(1 for tcInfo in tcIdx2tcInfo.values() if tcInfo['result'] == 1)
    return total_failing_tcs

def measure_scores(DB, PID, BID, FID, lineIdx2lineData):
    """
    Measure SBFL scores and save them to the database.
    :param DB: Database connection object.
    :param PID: Project ID.
    :param BID: Bug ID.
    :param FID: Fault index.
    :param lineIdx2lineData: Mapping of line indices to line data.
    """
    tcIdx2tcInfo = get_tcIdx2tcInfo(DB, FID)
    if not tcIdx2tcInfo:
        LOGGER.error(f"No test case information found for fault index {FID}.")
        raise ValueError(f"No test case information found for fault index {FID}.")
    LOGGER.info(f"Processing {len(tcIdx2tcInfo)} test cases for fault index {FID}.")

    # SBFL
    measure_spectrum(tcIdx2tcInfo, lineIdx2lineData)
    measure_sbfl_susp_scores(lineIdx2lineData)

    # MBFL
    total_failing_tcs = get_total_failing_tcs(tcIdx2tcInfo)
    if total_failing_tcs == 0:
        LOGGER.warning(f"No failing test cases found for fault index {FID}.")
        raise ValueError(f"No failing test cases found for fault index {FID}.")
    LOGGER.info(f"Total failing test cases: {total_failing_tcs}")

    lineIdx2mutation = get_lineIdx2mutation(DB, FID, lineIdx2lineData)
    measure_transition_cnts(lineIdx2mutation, tcIdx2tcInfo)
    # LOGGER.debug(json.dumps(lineIdx2mutation, indent=4))

    for mut_cnt in range(1, 11):
        using_mutants = get_using_mutants(lineIdx2mutation, mut_cnt)
        overall_data = get_overall_data(using_mutants, total_failing_tcs, mut_cnt)
        # LOGGER.debug(json.dumps(using_mutants, indent=4))

        measure_mbfl_susp_scores(
            lineIdx2lineData, using_mutants, mut_cnt, overall_data
        )

def write_ranks(lineIdx2lineData):
    """
    Calculate ranks for each suspiciousness score and add them to the lineIdx2lineData.
    Higher score → Lower (better) rank.
    If multiple lines have the same score, they share the upper bound rank.
    
    Example:
    lineIdx, score, rank
    23, 0.90, 1
    12, 0.38, 4  (equal scores get the last position)
    31, 0.38, 4
    21, 0.38, 4
    7,  0.21, 5
    
    :param lineIdx2lineData: Mapping of line indices to line data.
    """
    # Calculate ranks for SBFL formulas
    add_sbfl_ranks(lineIdx2lineData)

    # Calculate ranks for MBFL formulas
    add_mbfl_ranks(lineIdx2lineData, mut_cnt_range=(1, 11))
    
    LOGGER.info("Calculated ranks for all suspiciousness scores.")