import logging

LOGGER = logging.getLogger(__name__)

SBFL_FORMULA = [
    "tarantula", "ochiai", "dstar",
    "naish1", "naish2", "gp13"
]

TRANSITION_TYPES = {
    "type1": "result_transition",
    "type2": "exception_type_transition",
    "type3": "exception_msg_transition",
    "type4": "stacktrace_transition"
}

def calculate_ranks(score_pairs):
    """
    Calculate ranks for a list of (identifier, score) pairs.
    Higher score → Lower (better) rank.
    If multiple items have the same score, they share the upper bound rank.
    
    Example:
    item_id, score, rank
    23, 0.90, 1
    12, 0.38, 4  (equal scores get the last position)
    31, 0.38, 4
    21, 0.38, 4
    7,  0.21, 5
    
    :param score_pairs: List of (identifier, score) pairs
    :return: Dictionary mapping identifiers to their ranks
    """
    # Sort by score in descending order (higher score -> better rank)
    score_pairs.sort(key=lambda x: x[1], reverse=True)
    
    # First pass: Group scores and find the last position for each score
    score_to_rank = {}
    for idx, (_, score) in enumerate(score_pairs):
        # For each score, store the position of its last occurrence
        score_to_rank[score] = idx + 1
    
    # Second pass: Create mapping from identifier to rank
    id_to_rank = {}
    for item_id, score in score_pairs:
        id_to_rank[item_id] = score_to_rank[score]
    
    return id_to_rank

def add_sbfl_ranks(lineIdx2lineData):
    """
    Add ranks for each SBFL formula to lineIdx2lineData.
    
    :param lineIdx2lineData: Mapping of line indices to line data
    """
    for formula in SBFL_FORMULA:
        # Extract (lineIdx, score) pairs for this SBFL formula
        score_pairs = [(line_idx, data[formula]) for line_idx, data in lineIdx2lineData.items()]
        
        # Calculate ranks
        ranks = calculate_ranks(score_pairs)
        
        # Add ranks to lineIdx2lineData
        for line_idx, rank in ranks.items():
            lineIdx2lineData[line_idx][f"{formula}_rank"] = rank
    
    LOGGER.info(f"Added ranks for SBFL formulas: {', '.join(SBFL_FORMULA)}")

def add_mbfl_ranks(lineIdx2lineData, mut_cnt_range=(1, 11)):
    """
    Add ranks for each MBFL formula, mutation count, and transition type combination.
    
    :param lineIdx2lineData: Mapping of line indices to line data
    :param mut_cnt_range: Tuple of (min_mut_cnt, max_mut_cnt+1)
    """
    for mut_cnt in range(mut_cnt_range[0], mut_cnt_range[1]):
        for transition_type, transition_key in TRANSITION_TYPES.items():
            # For MUSE formula
            muse_key = f"mutCnt{mut_cnt}_{transition_key}_final_muse_score"
            
            # Check if the key exists in at least one line's data
            if any(muse_key in data for data in lineIdx2lineData.values()):
                # Extract (lineIdx, score) pairs for this MUSE formula
                score_pairs = [(line_idx, data.get(muse_key, float('-inf'))) 
                              for line_idx, data in lineIdx2lineData.items()]
                
                # Calculate ranks
                ranks = calculate_ranks(score_pairs)
                
                # Add ranks to lineIdx2lineData
                for line_idx, rank in ranks.items():
                    lineIdx2lineData[line_idx][f"{muse_key}_rank"] = rank
                
                LOGGER.debug(f"Added ranks for MUSE formula with mutCnt={mut_cnt}, transition={transition_type}")
            
            # For METAL formula
            metal_key = f"mutCnt{mut_cnt}_{transition_key}_final_metal_score"
            
            # Check if the key exists in at least one line's data
            if any(metal_key in data for data in lineIdx2lineData.values()):
                # Extract (lineIdx, score) pairs for this METAL formula
                score_pairs = [(line_idx, data.get(metal_key, float('-inf'))) 
                              for line_idx, data in lineIdx2lineData.items()]
                
                # Calculate ranks
                ranks = calculate_ranks(score_pairs)
                
                # Add ranks to lineIdx2lineData
                for line_idx, rank in ranks.items():
                    lineIdx2lineData[line_idx][f"{metal_key}_rank"] = rank
                
                LOGGER.debug(f"Added ranks for METAL formula with mutCnt={mut_cnt}, transition={transition_type}")
    
    LOGGER.info(f"Added ranks for MBFL formulas with mutation counts {mut_cnt_range[0]}-{mut_cnt_range[1]-1}")
