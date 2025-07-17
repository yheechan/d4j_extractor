import subprocess as sp
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
