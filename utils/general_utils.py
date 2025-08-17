import numpy as np
import logging

LOGGER = logging.getLogger(__name__)

def get_servers_list(file_path):
    """
    Read a file and return a list of servers.
    :param file_path: Path to the file containing server names.
    :return: List of server names.
    """
    try:
        with open(file_path, 'r') as file:
            servers = [line.strip() for line in file if line.strip()]
        LOGGER.info(f"Read {len(servers)} servers from {file_path}.")
        return servers
    except Exception as e:
        LOGGER.error(f"Failed to read server list from {file_path}: {e}")
        return []

def get_active_bugs_list(subject, D4J_HOME):
    """
    Get the list of active bugs for a given subject.
    :param subject: Subject name (e.g., 'Lang').
    :param D4J_HOME: Path to the Defects4J home directory.
    :return: List of active bugs.
    """
    bid_list = []
    try:
        csv_path = f"{D4J_HOME}/framework/projects/{subject}/active-bugs.csv"
        with open(csv_path, 'r') as file:
            lines = file.readlines()
            for line in lines[1:]: # Skip header
                parts = line.strip().split(",")
                if len(parts) < 2:
                    print(f"[WARN] Skipping malformed line in {subject}: {line.strip()}")
                    continue

                bug_id = parts[0].strip()
                if bug_id not in bid_list:
                    bid_list.append(bug_id)
        LOGGER.info(f"Found {len(bid_list)} active bugs for subject {subject}.")
        return bid_list
    except Exception as e:
        LOGGER.error(f"Failed to read active bugs for subject {subject}: {e}")
        return []

def getLinesExecutedByFailTcs(baseline_results):
    # get lines executed by all failing tcs
    linesExecutedByFailTcsBitVal = 0
    for failIdx in baseline_results["tcsResults"]["fail"]:
        tcInfo = baseline_results["tcIdx2tcInfo"][failIdx]
        covBitVal = tcInfo["covBitVal"]
        linesExecutedByFailTcsBitVal |= covBitVal

    return linesExecutedByFailTcsBitVal

def get_relevant_tests(baseline_results, linesExecutedByFailTcsBitVal):
    # get relevant tests
    relevant_tests = {}
    for tcIdx, tcInfo in baseline_results["tcIdx2tcInfo"].items():
        tcCovBitVal = tcInfo["covBitVal"]
        if linesExecutedByFailTcsBitVal & tcCovBitVal:
            relevant_tests[tcIdx] = tcInfo
    return relevant_tests

def get_relevant_lines(baseline_results, linesExecutedByFailTcsBitVal):
    # get relevant lines
    bitSeqStr = format(
        linesExecutedByFailTcsBitVal,
        f'0{len(baseline_results["lineIdx2lineInfo"])}b'
    )

    relevant_lines = {}
    for lineIdx, lineInfo in baseline_results["lineIdx2lineInfo"].items():
        if bitSeqStr[lineIdx] == '1':
            relevant_lines[lineIdx] = lineInfo

    return relevant_lines

def set_relevant_line_cov_bit(relevant_tests, relevant_lines, baseline_results):
    for tcIdx, tcInfo in relevant_tests.items():
        tcCovBitVal = tcInfo["covBitVal"]

        fullCovBitSeqStr = format(
            tcCovBitVal,
            f'0{len(baseline_results["lineIdx2lineInfo"])}b'
        )
        relCovBitSeqStr = ""

        for lineIdx, lineInfo in relevant_lines.items():
            relCovBitSeqStr += fullCovBitSeqStr[lineIdx]
        
        tcInfo["relCovBitVal"] = int(relCovBitSeqStr, 2)

def reset_idx(data):
    newData = {}
    newIdx = -1
    for idx, value in data.items():
        newIdx += 1
        newData[newIdx] = value
    return newData

def cosine_similarity(bit_sequence_1, bit_sequence_2):
    v1 = np.array(list(bit_sequence_1)).astype(float)
    v2 = np.array(list(bit_sequence_2)).astype(float)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    dot_product = np.dot(v1, v2)
    magnitude_v1 = np.linalg.norm(v1)
    magnitude_v2 = np.linalg.norm(v2)
    return (dot_product / (magnitude_v1 * magnitude_v2)).item()
