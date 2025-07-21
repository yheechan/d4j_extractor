from utils.rank_utils import *

def test_calculate_ranks():
    score_pairs = [
        ("item1", 0.90),
        ("item2", 0.38),
        ("item3", 0.38),
        ("item4", 0.38),
        ("item5", 0.21)
    ]
    
    expected_ranks = {
        "item1": 1,
        "item2": 4,
        "item3": 4,
        "item4": 4,
        "item5": 5
    }
    
    ranks = calculate_ranks(score_pairs)
    
    assert ranks == expected_ranks, f"Expected {expected_ranks}, but got {ranks}"