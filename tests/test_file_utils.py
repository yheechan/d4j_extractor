from dotenv import load_dotenv
import os

from utils.file_utils import *


def test_make_directory():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_path = server_home + "test_directory"

    res = make_directory(mock_path, mock_server)
    assert res is True, f"Failed to create directory {mock_path} on server {mock_server}"


def test_delete_directory():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_path = server_home + "test_directory"
    
    test_make_directory()  # Ensure the directory exists before trying to delete it
    
    res = delete_directory(mock_path, mock_server)
    assert res is True, f"Failed to delete directory {mock_path} on server {mock_server}"

def test_send_file():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_src = "mock_file.txt"
    mock_dest = server_home + "test_directory/"

    # Create a mock file to send
    with open(mock_src, 'w') as f:
        f.write("This is a test file.")

    test_make_directory()  # Ensure the destination directory exists

    res = send_file(mock_src, mock_dest, mock_server)
    assert res is True, f"Failed to send file {mock_src} to {mock_dest} on server {mock_server}"

    # Clean up the mock file
    os.remove(mock_src)

def test_chmod_file():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_path = server_home + "test_directory/mock_file.txt"

    test_send_file()  # Ensure the file exists before trying to change permissions

    mode = "755"  # Example mode
    res = chmod_file(mock_path, mode, mock_server)
    assert res is True, f"Failed to change permissions of file {mock_path} on server {mock_server}"

def test_receive_file():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_src = server_home + "test_directory/mock_file.txt"
    mock_dest = "received_mock_file.txt"

    test_send_file()  # Ensure the file exists on the server before trying to receive it

    # Now test receiving the file
    res = receive_file(mock_src, mock_dest, mock_server)
    assert res is True, f"Failed to receive file {mock_src} to {mock_dest} from server {mock_server}"
    assert os.path.exists(mock_dest), f"File {mock_dest} was not received successfully."

    # Clean up the received file
    os.remove(mock_dest)

def test_delete_file():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_path = server_home + "test_directory/mock_file.txt"

    test_send_file()  # Ensure the file exists before trying to delete it

    res = delete_file(mock_path, mock_server)
    assert res is True, f"Failed to delete file {mock_path} on server {mock_server}"

def test_send_directory():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_src = "mock_test_directory"
    os.makedirs(mock_src, exist_ok=True)  # Ensure the source directory exists
    mock_file = os.path.join(mock_src, "mock_file.txt")
    with open(mock_file, 'w') as f:
        f.write("This is a test file in the directory.")

    mock_dest = server_home + "test_directory/"

    # Ensure the source directory exists
    test_make_directory()

    res = send_directory(mock_src, mock_dest, mock_server)
    assert res is True, f"Failed to send directory {mock_src} to {mock_dest} on server {mock_server}"

    # Clean up the mock directory and file
    os.remove(mock_file)
    os.rmdir(mock_src)

def test_receive_directory():
    load_dotenv()
    server_home = os.environ.get("SERVER_HOME")
    assert server_home is not None

    mock_server = os.environ.get("TEST_SERVER")
    mock_src = server_home + "test_directory/mock_test_directory"
    mock_dest = "."

    test_send_directory()  # Ensure the directory exists on the server before trying to receive it

    # Now test receiving the directory
    res = receive_directory(mock_src, mock_dest, mock_server)
    assert res is True, f"Failed to receive directory {mock_src} to {mock_dest} from server {mock_server}"
    assert os.path.exists(os.path.join(mock_dest, "mock_test_directory")), f"Directory {mock_dest}/mock_test_directory was not received successfully."

    # Clean up the received directory
    received_dir = os.path.join(mock_dest, "mock_test_directory")
    if os.path.exists(received_dir):
        for root, dirs, files in os.walk(received_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(received_dir)
