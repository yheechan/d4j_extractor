"""
File utility functions for managing file/directory operations on remote servers.
    - make, delete directories
    - send, receive, delete file/directories
    - copy file/directories
"""

import subprocess as sp
import logging

LOGGER = logging.getLogger(__name__)

def make_directory(path, server):
    """
    Create a directory on the remote server.
    :param path: Path of the directory to create.
    :param server: Remote server object.
    :return: True if directory creation is successful, False otherwise.
    """
    try:
        sp.check_call(["ssh", f"{server}", f"mkdir -p {path}"])
        LOGGER.info(f"Directory {path} created on server {server}.")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to create directory {path}: {e}")
        return False
    
def delete_directory(path, server):
    """
    Delete a directory on the remote server.
    :param path: Path of the directory to delete.
    :param server: Remote server object.
    :return: True if directory deletion is successful, False otherwise.
    """
    try:
        sp.check_call(["ssh", f"{server}", f"rm -rf {path}"])
        LOGGER.info(f"Directory {path} deleted on server {server}.")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to delete directory {path}: {e}")
        return False

def send_file(src, dest, server):
    """
    Send a file to the remote server.
    :param src: Source file path.
    :param dest: Destination path on the remote server.
    :param server: Remote server object.
    :return: True if file transfer is successful, False otherwise.
    """
    try:
        sp.check_call(["rsync", "-t", "-r", f"{src}", f"{server}:{dest}"])
        LOGGER.info(f"File {src} sent to {server}:{dest}.")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to send file {src} to {server}:{dest}: {e}")
        return False

def receive_file(src, dest, server):
    """
    Receive a file from the remote server.
    :param src: Source file path on the remote server.
    :param dest: Destination path on the local machine.
    :param server: Remote server object.
    :return: True if file transfer is successful, False otherwise.
    """
    try:
        sp.check_call(["rsync", "-t", "-r", f"{server}:{src}", f"{dest}"])
        LOGGER.info(f"File {server}:{src} received to {dest}.")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to receive file {server}:{src} to {dest}: {e}")
        return False

def delete_file(path, server):
    """
    Delete a file on the remote server.
    :param path: Path of the file to delete.
    :param server: Remote server object.
    :return: True if file deletion is successful, False otherwise.
    """
    try:
        sp.check_call(["ssh", f"{server}", f"rm -f {path}"])
        LOGGER.info(f"File {path} deleted on server {server}.")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to delete file {path}: {e}")
        return False

def send_directory(src, dest, server):
    """
    Send a directory to the remote server.
    :param src: Source directory path.
    :param dest: Destination path on the remote server.
    :param server: Remote server object.
    :return: True if directory transfer is successful, False otherwise.
    """
    try:
        sp.check_call(["rsync", "-t", "-r", f"{src}", f"{server}:{dest}"])
        LOGGER.info(f"Directory {src} sent to {server}:{dest}.")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to send directory {src} to {server}:{dest}: {e}")
        return False

def receive_directory(src, dest, server):
    """
    Receive a directory from the remote server.
    :param src: Source directory path on the remote server.
    :param dest: Destination path on the local machine.
    :param server: Remote server object.
    :return: True if directory transfer is successful, False otherwise.
    """
    try:
        sp.check_call(["rsync", "-t", "-r", f"{server}:{src}", f"{dest}"])
        LOGGER.info(f"Directory {server}:{src} received to {dest}.")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to receive directory {server}:{src} to {dest}: {e}")
        return False
