from dotenv import load_dotenv
import os

from utils.command_utils import *

def test_run_command():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_command = "echo 'Hello, World!'"

    res = execute_command(mock_command, mock_server)
    assert res is True, f"Failed to run command '{mock_command}' on server {mock_server}"