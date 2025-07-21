import logging
import json
import math

LOGGER = logging.getLogger(__name__)

TRANSITION_TYPES = {
    "type1": "result_transition",
    "type2": "exception_type_transition",
    "type3": "exception_msg_transition",
    "type4": "stacktrace_transition"
}


def get_using_mutants(lineIdx2mutation, mut_cnt):
    """
    Get the mutants that are being used for the current mutation count.
    :param lineIdx2mutation: Mapping of line indices to mutation data.
    :param mut_cnt: Current mutation count.
    :return: Dictionary of using mutants.
    """
    using_mutants = {}
    for line_idx, mutation_list in lineIdx2mutation.items():
        if len(mutation_list) >= mut_cnt:
            using_mutants[line_idx] = mutation_list[:mut_cnt]
        else:
            using_mutants[line_idx] = mutation_list
    return using_mutants

def get_transition_counts(transition_bit_seq, tcIdx2tcInfo):
    f2p, p2f, f2f, p2p = 0, 0, 0, 0
    
    for tcIdx, bit_val in enumerate(transition_bit_seq):
        baseline_outcome = 1 if tcIdx2tcInfo[tcIdx]['result'] == 1 else 0

        if baseline_outcome == 1: # failing
            if bit_val == '1':
                f2p += 1
            else:
                f2f += 1
        else: # passing
            if bit_val == '1':
                p2f += 1
            else:
                p2p += 1

    return f2p, p2f, f2f, p2p

def measure_transition_cnts(lineIdx2mutation, tcIdx2tcInfo):
    """
    Measure the transition counts for each mutant.
    :param lineIdx2mutation: Mapping of line indices to mutation data.
    """
    for line_idx, mutation_list in lineIdx2mutation.items():
        for mutation_data in mutation_list:
            mutation_idx = mutation_data['mutation_idx']
            
            for transition_type, transition_key in TRANSITION_TYPES.items():                
                f2p, p2f, f2f, p2p = get_transition_counts(mutation_data[transition_key], tcIdx2tcInfo)

                mutation_data[transition_key] = {
                    "f2p": f2p,
                    "p2f": p2f,
                    "f2f": f2f,
                    "p2p": p2p
                }

def get_overall_data(using_mutants, total_failing_tcs, mut_cnt):
    overall_data = {
        "total_failing_tcs": total_failing_tcs,
        "total_mutants": 0,

        f"mutCnt{mut_cnt}_type1_total_f2p": 0,
        f"mutCnt{mut_cnt}_type1_total_p2f": 0,
        f"mutCnt{mut_cnt}_type1_total_f2f": 0,
        f"mutCnt{mut_cnt}_type1_total_p2p": 0,

        f"mutCnt{mut_cnt}_type2_total_f2p": 0,
        f"mutCnt{mut_cnt}_type2_total_p2f": 0,
        f"mutCnt{mut_cnt}_type2_total_f2f": 0,
        f"mutCnt{mut_cnt}_type2_total_p2p": 0,

        f"mutCnt{mut_cnt}_type3_total_f2p": 0,
        f"mutCnt{mut_cnt}_type3_total_p2f": 0,
        f"mutCnt{mut_cnt}_type3_total_f2f": 0,
        f"mutCnt{mut_cnt}_type3_total_p2p": 0,

        f"mutCnt{mut_cnt}_type4_total_f2p": 0,
        f"mutCnt{mut_cnt}_type4_total_p2f": 0,
        f"mutCnt{mut_cnt}_type4_total_f2f": 0,
        f"mutCnt{mut_cnt}_type4_total_p2p": 0
    }

    for line_idx, mutation_list in using_mutants.items():
        overall_data["total_mutants"] += len(mutation_list)

        for mutation_data in mutation_list:
            for transition_type, transition_key in TRANSITION_TYPES.items():
                f2p = mutation_data[transition_key]["f2p"]
                p2f = mutation_data[transition_key]["p2f"]
                f2f = mutation_data[transition_key]["f2f"]
                p2p = mutation_data[transition_key]["p2p"]

                overall_data[f"mutCnt{mut_cnt}_{transition_type}_total_f2p"] += f2p
                overall_data[f"mutCnt{mut_cnt}_{transition_type}_total_p2f"] += p2f
                overall_data[f"mutCnt{mut_cnt}_{transition_type}_total_f2f"] += f2f
                overall_data[f"mutCnt{mut_cnt}_{transition_type}_total_p2p"] += p2p

    return overall_data

def measure_muse_on_line(using_mutants, overall_f2p, overall_p2f, transition_key, mut_cnt):
    abs_muts = len(using_mutants)

    line_total_f2p = 0
    line_total_p2f = 0

    for mutant in using_mutants:
        f2p = mutant[transition_key]["f2p"]
        p2f = mutant[transition_key]["p2f"]

        line_total_f2p += f2p
        line_total_p2f += p2f

    muse_1 = (1 / ((abs_muts + 1) * (overall_f2p + 1)))
    muse_2 = (1 / ((abs_muts + 1) * (overall_p2f + 1)))

    muse_3 = muse_1 * line_total_f2p
    muse_4 = muse_2 * line_total_p2f

    final_muse_score = muse_3 - muse_4

    muse_data = {
        f"mutCnt{mut_cnt}_{transition_key}_abs_muts": abs_muts,
        f"mutCnt{mut_cnt}_{transition_key}_line_total_f2p": line_total_f2p,
        f"mutCnt{mut_cnt}_{transition_key}_line_total_p2f": line_total_p2f,
        f"mutCnt{mut_cnt}_{transition_key}_muse_1": muse_1,
        f"mutCnt{mut_cnt}_{transition_key}_muse_2": muse_2,
        f"mutCnt{mut_cnt}_{transition_key}_muse_3": muse_3,
        f"mutCnt{mut_cnt}_{transition_key}_muse_4": muse_4,
        f"mutCnt{mut_cnt}_{transition_key}_final_muse_score": final_muse_score,
    }

    return muse_data

def measure_metal_on_line(using_mutants, total_failing_tcs, transition_key, mut_cnt):
    metal_scores = []

    for mutant in using_mutants:
        f2p = mutant[transition_key]["f2p"]
        p2f = mutant[transition_key]["p2f"]

        score = 0.0
        if f2p + p2f == 0:
            score = 0.0
        else:
            score = ((f2p) / math.sqrt(total_failing_tcs * (f2p + p2f)))

        metal_scores.append(score)

    if len(metal_scores) == 0:
        metal_score = 0.0
    else:
        metal_score = max(metal_scores)

    metal_data = {
        f"mutCnt{mut_cnt}_{transition_key}_final_metal_score": metal_score
    }

    return metal_data

def measure_mbfl_susp_scores(lineIdx2lineData, using_mutants, mut_cnt, overall_data):
    default_values = {}
    for transition_type, transition_key in TRANSITION_TYPES.items():
        default_values[f"mutCnt{mut_cnt}_{transition_type}_abs_muts"] = 0
        default_values[f"mutCnt{mut_cnt}_{transition_type}_line_total_f2p"] = -10.0
        default_values[f"mutCnt{mut_cnt}_{transition_type}_line_total_p2f"] = -10.0
        default_values[f"mutCnt{mut_cnt}_{transition_type}_muse_1"] = -10.0
        default_values[f"mutCnt{mut_cnt}_{transition_type}_muse_2"] = -10.0
        default_values[f"mutCnt{mut_cnt}_{transition_type}_muse_3"] = -10.0
        default_values[f"mutCnt{mut_cnt}_{transition_type}_muse_4"] = -10.0
        default_values[f"mutCnt{mut_cnt}_{transition_type}_final_muse_score"] = -10.0
        default_values[f"mutCnt{mut_cnt}_{transition_type}_final_metal_score"] = -10.0

    for lineIdx in lineIdx2lineData.keys():
        if lineIdx not in using_mutants:
            lineIdx2lineData[lineIdx] = {**lineIdx2lineData[lineIdx], **default_values}
            continue
        
        for transition_type, transition_key in TRANSITION_TYPES.items():
            overall_f2p = overall_data[f"mutCnt{mut_cnt}_{transition_type}_total_f2p"]
            overall_p2f = overall_data[f"mutCnt{mut_cnt}_{transition_type}_total_p2f"]
            total_failing_tcs = overall_data["total_failing_tcs"]

            muse_data = measure_muse_on_line(using_mutants[lineIdx], overall_f2p, overall_p2f, transition_key, mut_cnt)
            metal_data = measure_metal_on_line(using_mutants[lineIdx], total_failing_tcs, transition_key, mut_cnt)

            lineIdx2lineData[lineIdx] = {**lineIdx2lineData[lineIdx], **muse_data, **metal_data}