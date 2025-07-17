from dotenv import load_dotenv
import os

from utils.general_utils import *

def test_get_servers_list():
    load_dotenv()
    SERVER_LIST_FILE = os.environ.get("SERVER_LIST_FILE")
    assert SERVER_LIST_FILE is not None, "SERVER_LIST_FILE environment variable is not set."

    # Assuming get_servers_list returns a list of server names
    server_list = get_servers_list(SERVER_LIST_FILE)

    assert isinstance(server_list, list), "get_servers_list should return a list."
    assert len(server_list) > 0, "Server list should not be empty."
    for server in server_list:
        assert isinstance(server, str), "Each server name should be a string."

def test_get_active_bugs_list():
    load_dotenv()
    D4J_HOME = os.environ.get("D4J_HOME")
    assert D4J_HOME is not None, "D4J_HOME environment variable is not set."

    subject = "Lang"
    bid_list = get_active_bugs_list(subject, D4J_HOME)

    assert isinstance(bid_list, list), "get_active_bugs_list should return a list."
    assert len(bid_list) > 0, f"Active bugs list for subject {subject} should not be empty."
    for bid in bid_list:
        assert isinstance(bid, str), "Each bug ID should be a string."

def test_execute_command():
    load_dotenv()
    mock_server = os.environ.get("TEST_SERVER")
    assert mock_server is not None, "TEST_SERVER environment variable is not set."

    command = "echo 'Hello, World!'"
    
    # Assuming execut_command returns True if the command was executed successfully
    result = execut_command(command, mock_server)

    assert result is True, f"Command '{command}' should be executed successfully on server {mock_server}."