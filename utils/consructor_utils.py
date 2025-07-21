
import logging

LOGGER = logging.getLogger(__name__)

def get_bid2fid(DB, PID, EL):
        """
        Get the mapping of bug IDs to line numbers from the database.
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
            return line_data['method']
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
                nearest_line = line_data

    if nearest_line:
        LOGGER.info(f"Found nearest line for {file_name}:{line_num} - {nearest_line['line_num']}")
    else:
        LOGGER.warning(f"No nearest line found for {file_name}:{line_num}.")

    return nearest_line
