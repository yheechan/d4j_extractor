import re
import math

TRACE_PATTERN = re.compile(r'\s*at\s+([\w\.$]+)\(([\w\.]+):(\d+)\)')

import logging

LOGGER = logging.getLogger(__name__)

def get_st_list(tcIdx2tcInfo):
    st_list = []
    for tcIdx, tcInfo in tcIdx2tcInfo.items():
        stack_trace = tcInfo['stack_trace']
        if stack_trace:
            st_list.append(stack_trace.lower())
    return st_list

def measure_ST_relevance(tcIdx2tcInfo, lineIdx2lineData, scale=1.0):
    first_key = next(iter(lineIdx2lineData))
    if "st_relevance" in lineIdx2lineData[first_key]:
        LOGGER.debug("Skipping st relevance measurement")
        return

    st_list = get_st_list(tcIdx2tcInfo)
    parsed_trace = {}
    for st in st_list:
        for line in st.splitlines():
            match = TRACE_PATTERN.search(line)
            if match:
                fullMethodPath, classFileName, lineNumber = match.groups()
                # We simplify the key to just the class and method name
                # e.g., WordUtils.abbreviate from org.apache.commons.lang.WordUtils.abbreviate
                key = ".".join(fullMethodPath.split('.')[-2:])
                className, methodName = key.split('.')
                if className not in parsed_trace:
                    parsed_trace[className] = {}
                if methodName not in parsed_trace[className]:
                    parsed_trace[className][methodName] = []
                parsed_trace[className][methodName].append(int(lineNumber))

    for line_idx, line_data in lineIdx2lineData.items():
        st_relevance_score = 0.0

        fileName = line_data["file"]
        className = line_data["class"]
        methodName = line_data["method"]
        lineNum = line_data["line_num"]

        pp_fileName = fileName.strip().split("/")[-1].lower()
        candidate_className = className.strip().split(".")[-1].lower()
        candidate_methodName = methodName.strip().split("(")[0].lower()
        candidate_lineNum = lineNum

        if candidate_className in parsed_trace:
            if candidate_methodName in parsed_trace[candidate_className]:
                line_numbers = parsed_trace[candidate_className][candidate_methodName]
                
                for trace_line_num in line_numbers:
                    distance = abs(trace_line_num - candidate_lineNum)
                    score = math.exp(-(distance**2)/scale)
                    if score > st_relevance_score:
                        st_relevance_score = score

        lineIdx2lineData[line_idx]["st_relevance"] = st_relevance_score

# def add_ST_rank(lineIdx2lineData):
#     formula = "st_rank"
#     # Extract (lineIdx, score) pairs for this SBFL formula
#     score_pairs = [(line_idx, data[formula]) for line_idx, data in lineIdx2lineData.items()]
    
#     # Calculate ranks
#     ranks = calculate_ranks(score_pairs)
    
#     # Add ranks to lineIdx2lineData
#     for line_idx, rank in ranks.items():
#         lineIdx2lineData[line_idx][f"{formula}_rank"] = rank