import os
import subprocess as sp
import multiprocessing

# Servers list
servers = {    
    "faster4.swtv",
    "faster5.swtv",
    "faster7.swtv",
    "faster8.swtv",
    "faster14.swtv",
    "faster15.swtv",
    "faster17.swtv",
    "faster18.swtv",
    "faster19.swtv",
    "faster20.swtv",
    "faster23.swtv",
    "faster24.swtv",
    "faster25.swtv",
    "faster26.swtv",
    "faster27.swtv",
    "faster29.swtv",
    "faster31.swtv",
    "faster32.swtv",
    "faster33.swtv",
    "faster34.swtv",
    "faster36.swtv",
    "faster37.swtv",
    "faster38.swtv",
    "faster39.swtv",
    "faster40.swtv",
    "faster41.swtv",
    "faster42.swtv",
    "faster44.swtv",
    "faster45.swtv",
    "faster46.swtv",
    "faster47.swtv",
    "faster48.swtv",
    "faster50.swtv",
    "faster51.swtv"
}

# Function to execute the zip command for each core on a server
def execute_command(server, core_name):
    try:
        # Construct the command
        command = [
            "ssh", f"{server}",
            f"cd /home/yangheechan/FL-dataset-generation-opencv_core/work/opencv_core/working_env/{server}/{core_name}/ && zip -rq coverage.zip coverage/"
        ]
        # Execute the command
        sp.check_call(command)

        # Print success message (for debugging purposes)
        print(f"Executed on {server}:{core_name}")
    except sp.CalledProcessError as e:
        print(f"Error executing on {server}:{core_name} - {e}")
import time
# Function to handle each server with all core* directories
def handle_server(server):
    for i in range(0, 16):
        core_name = f"core{i}"
        print(f"Executing on {server}:{core_name}")
        execute_command(server, core_name)

# Main function to execute multiprocessing with a maximum of 10 processes
if __name__ == "__main__":
    # Create a multiprocessing pool with a maximum of 10 processes
    with multiprocessing.Pool(processes=10) as pool:
        # Map the handle_server function to the servers list
        pool.map(handle_server, servers)

    print("All commands executed.")
