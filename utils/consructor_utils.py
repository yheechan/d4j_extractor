from utils.sbfl_utils import *
from utils.mbfl_utils import *
from utils.rank_utils import add_sbfl_ranks, add_mbfl_ranks
from utils.st_utils import *


import logging
import json
import random
import time

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
        return (None, None)

    return nearest_line

def assign_groundtruth(DB, PID, BID, lineIdx2lineData):
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
    :param PID: Project ID.
    :param BID: Bug ID.
    :param FID: Fault index.
    :return: List of test case information.
    """
    col = [
        "tc_idx", "test_name", "result", "execution_time_ms",
        "bit_sequence_length", "line_coverage_bit_sequence",
        "stacktrace"
    ]
    col_str = ", ".join(col)
    tc_info = DB.read(
        "d4j_tc_info",
        columns=col_str,
        conditions={
            "fault_idx": FID
        }
    )

    tcIdx2tcInfo = {}
    for tc_data in tc_info:
        tc_idx, test_name, result, \
            execution_time_ms, bit_sequence_length, \
            line_coverage_bit_sequence, stacktrace = tc_data
        
        tcIdx2tcInfo[tc_idx] = {
            "test_name": test_name,
            "result": result,
            "execution_time_ms": execution_time_ms,
            "bit_sequence_length": bit_sequence_length,
            "line_coverage_bit_sequence": line_coverage_bit_sequence,
            "stack_trace": stacktrace
        }

    return tcIdx2tcInfo

def combine_transitions(result_transition, exception_type_transition,
                        exception_msg_transition, stacktrace_transition):
    """
    each type transition is a string of '0's and '1's.
    Combine by or operation on each bit
    :param result_transition: Result transition bit sequence.
    :param exception_type_transition: Exception type transition bit sequence.
    :param exception_msg_transition: Exception message transition bit sequence.
    :param stacktrace_transition: Stacktrace transition bit sequence.
    :return: Combined transition bit sequence.
    """

    
    # Alternative Method 2: Using bitwise operations on integers (fastest for very long strings)
    # Convert binary strings to integers, perform OR operation, convert back
    int_result = (int(result_transition, 2) | 
                  int(exception_type_transition, 2) |
                  int(exception_msg_transition, 2) | 
                  int(stacktrace_transition, 2))
    return format(int_result, f'0{len(result_transition)}b')

def check4methodMatch(line_method, mutation_methods):
    """
    Check if the line method matches any of the mutation methods.
    :param line_method: The method name of the line.
    :param mutation_methods: A list of mutation method names.
    :return: True if there is a match, False otherwise.
    """
    for mutation_method in mutation_methods:
        if mutation_method in line_method:
            return mutation_method
    return False

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

    # mutationClass2Method2lineNum2mutationInfo
    mutation_dict = {}
    for mutation in mutation_info:
        mutation_idx, class_name, method, line, \
                result_transition, exception_type_transition, \
                exception_msg_transition, stacktrace_transition, \
                status, num_tests_run = mutation
        
        all_types_transition = combine_transitions(
            result_transition, exception_type_transition,
            exception_msg_transition, stacktrace_transition
        )
        
        if class_name not in mutation_dict:
            mutation_dict[class_name] = {}
        if method not in mutation_dict[class_name]:
            mutation_dict[class_name][method] = {}
        if line not in mutation_dict[class_name][method]:
            mutation_dict[class_name][method][line] = []
        mutation_dict[class_name][method][line].append({
            "mutation_idx": mutation_idx,
            "result_transition": result_transition,
            "exception_type_transition": exception_type_transition,
            "exception_msg_transition": exception_msg_transition,
            "stacktrace_transition": stacktrace_transition,
            "all_types_transition": all_types_transition,
            "status": status,
            "num_tests_run": num_tests_run
        })
    
    lineIdx2mutation = {}
    for lineIdx, line_data in lineIdx2lineData.items():
        lineIdx2mutation[lineIdx] = []
        line_class = line_data['class']
        line_method = line_data['method']
        line_num = line_data['line_num']

        line_start_time = time.time()
        if line_class in mutation_dict:
            method_key = check4methodMatch(line_method, mutation_dict[line_class].keys())
            if method_key:
                if line_num in mutation_dict[line_class][method_key]:
                    lineIdx2mutation[lineIdx].extend(mutation_dict[line_class][method_key][line_num])
        line_time = time.time() - line_start_time
        LOGGER.debug(f"[{FID}b] get_lineIdx2mutation took {line_time:.2f} seconds. with mutation cnt {len(mutation_info)}")

    # shuffle the mutation list for each line
    mut_exists = False
    for line_idx, mutation_list in lineIdx2mutation.items():
        if mutation_list:
            random.shuffle(mutation_list)
            mut_exists = True
    
    if not mut_exists:
        LOGGER.warning(f"No mutations found for fault index {FID}.")

    return lineIdx2mutation

def get_total_failing_tcs(tcIdx2tcInfo):
    """
    Get the total number of failing test cases.
    :param tcIdx2tcInfo: Mapping of test case indices to test case information.
    :return: Total number of failing test cases.
    """
    total_failing_tcs = sum(1 for tcInfo in tcIdx2tcInfo.values() if tcInfo['result'] == 1)
    return total_failing_tcs

def measure_scores(EXP_CONFIG, DB, FID, lineIdx2lineData, rid=None):
    """
    Measure SBFL scores and save them to the database.
    :param EXP_CONFIG: Experiment configuration dictionary.
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


    # Stack Trace Relevance
    st_start_time = time.time()
    measure_ST_relevance(tcIdx2tcInfo, lineIdx2lineData)
    st_time = time.time() - st_start_time
    LOGGER.debug(f"[rid{rid}-{FID}b] Stack Trace Relevance took {st_time:.2f} seconds.")
    # add_ST_rank(lineIdx2lineData)

    # SBFL
    sbfl_start_time = time.time()
    measure_spectrum(tcIdx2tcInfo, lineIdx2lineData)
    measure_sbfl_susp_scores(lineIdx2lineData)
    # Calculate ranks for SBFL formulas
    add_sbfl_ranks(lineIdx2lineData)
    sbfl_time = time.time() - sbfl_start_time
    LOGGER.debug(f"[rid{rid}-{FID}b] SBFL took {sbfl_time:.2f} seconds.")
    sorted_lineIdx = get_sorted_lineIdx(lineIdx2lineData, EXP_CONFIG["line_selection_formula"])



    # MBFL
    total_failing_tcs = get_total_failing_tcs(tcIdx2tcInfo)
    if total_failing_tcs == 0:
        LOGGER.warning(f"No failing test cases found for fault index {FID}.")
        raise ValueError(f"No failing test cases found for fault index {FID}.")
    LOGGER.info(f"Total failing test cases: {total_failing_tcs}")

    get_lineIdx2lineData_start_time = time.time()
    lineIdx2mutation = get_lineIdx2mutation(DB, FID, lineIdx2lineData)
    get_lineIdx2lineData_time = time.time() - get_lineIdx2lineData_start_time
    LOGGER.debug(f"[rid{rid}-{FID}b] get_lineIdx2lineData took {get_lineIdx2lineData_time:.2f} seconds.")

    measure_transition_start_time = time.time()
    measure_transition_counts(lineIdx2mutation, tcIdx2tcInfo, EXP_CONFIG["tcs_reduction"])
    measure_transition_time = time.time() - measure_transition_start_time
    LOGGER.debug(f"[rid{rid}-{FID}b] measure_transition_counts took {measure_transition_time:.2f} seconds.")

    mbfl_start_time = time.time()
    for line_cnt in EXP_CONFIG["target_lines"]:
        target_line_perc = line_cnt / 100.0
        selection_amount = int(len(sorted_lineIdx) * target_line_perc)
        selected_lineIdx = sorted_lineIdx[:selection_amount]

        LOGGER.info(f"Selected {len(selected_lineIdx)} lines for target line percentage {target_line_perc:.2%}.")

        for mut_cnt in EXP_CONFIG["mutation_cnt"]:
            first_key = next(iter(lineIdx2mutation))
            if f"lineCnt{line_cnt}_mutCnt{mut_cnt}tcs{EXP_CONFIG['tcs_reduction']}_all_types_transition_final_metal_score_rank" in lineIdx2lineData[first_key]:
                LOGGER.debug(f"Skipping line count {line_cnt} and mutation count {mut_cnt} as scores already calculated.")
                continue

            get_using_mutants_start_time = time.time()
            using_mutants = get_using_mutants(lineIdx2mutation, selected_lineIdx, mut_cnt)
            get_using_mutants_time = time.time() - get_using_mutants_start_time
            LOGGER.debug(f"[rid{rid}-{FID}b] get_using_mutants took {get_using_mutants_time:.2f} seconds.")

            get_overall_data_start_time = time.time()
            overall_data = get_overall_data(using_mutants, total_failing_tcs, line_cnt, mut_cnt, EXP_CONFIG["tcs_reduction"])
            get_overall_data_time = time.time() - get_overall_data_start_time
            LOGGER.debug(f"[rid{rid}-{FID}b] get_overall_data took {get_overall_data_time:.2f} seconds.")

            measure_mbfl_score_time = time.time()
            measure_mbfl_susp_scores(
                lineIdx2lineData, using_mutants, line_cnt, mut_cnt, EXP_CONFIG["tcs_reduction"], overall_data
            )
            measure_mbfl_score_time = time.time() - measure_mbfl_score_time
            LOGGER.debug(f"[rid{rid}-{FID}b] measure_mbfl_susp_scores took {measure_mbfl_score_time:.2f} seconds.")

    # Calculate ranks for MBFL formulas
    add_mbfl_ranks(lineIdx2lineData, EXP_CONFIG)

    mbfl_time = time.time() - mbfl_start_time
    LOGGER.debug(f"[rid{rid}-{FID}b] MBFL took {mbfl_time:.2f} seconds.")
