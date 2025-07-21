# Rank Calculation Integration for lineIdx2lineData
The dataset lineIdx2lineData is a dictionary where:

    Key: lineIdx

    Value: dynamic features, which include:

        Whether the line is faulty or not

        SBFL suspiciousness scores

        MBFL suspiciousness scores (based on various values of mutCnt and transition types)

# Goal
You want to add new keys for each line that include rank values for:

    Each SBFL formula (e.g., Tarantula, Ochiai, etc.)

    Each combination of:

        MBFL formula (e.g., muse, metal)

        mutCnt value

        transition type

The rank should be calculated within each bug.

# Ranking Rule
    Higher score → Lower (better) rank

    If multiple lines have the same score, they share the upper bound rank

    Example:
    ```
    lineIdx, score, rank
    23, 0.90, 1
    12, 0.38, 4
    31, 0.38, 4
    21, 0.38, 4
    7,  0.21, 5
    ...
    ```

# Provided Files
You can refer to the following files:

    main.py

    constructor_engine.py

    constructor_utils.py

    mbfl_utils.py

    sbfl_utils.py