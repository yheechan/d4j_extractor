"""
File utility functions for executing commands on remote servers.
"""

import subprocess as sp
import logging

LOGGER = logging.getLogger(__name__)

def execute_command(command, server):
    """
    Execute a command on the remote server.
    :param command: Command to execute.
    :param server: Remote server object.
    :return: True if command execution is successful, False otherwise.
    """
    try:
        sp.check_call(["ssh", f"{server}", command], stderr=sp.DEVNULL, stdout=sp.DEVNULL)
        LOGGER.info(f"Command '{command}' executed successfully on server {server}.")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to execute command '{command}' on server {server}: {e}")
        return False