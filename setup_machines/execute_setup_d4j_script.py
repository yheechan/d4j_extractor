# This script is to execute the setup_d4j.sh script on multiple machines
# specifically it will run 5 batch at a time

import os
import subprocess
    
def execute_setup_script():
    script_path = os.path.join(os.path.dirname(__file__), '../scripts/setup_d4j.sh')
    if not os.path.exists(script_path):
        print(f"Script {script_path} does not exist.")
        return

    # Read the list of hosts from the file
    hosts_file = os.path.expanduser('~/.hosts/mbfl_servers')
    if not os.path.exists(hosts_file):
        print(f"Hosts file {hosts_file} does not exist.")
        return

    with open(hosts_file, 'r') as f:
        hosts = f.read().splitlines()

    for host in hosts:
        host = host.strip()
        if not host:
            continue
        command = f'scp {script_path} {USERNAME}@{host}:{HOME_DIR}'
        chgmod_command = f'ssh {USERNAME}@{host} "chmod +x {HOME_DIR}/setup_d4j.sh"'
        try:
            subprocess.run(command, shell=True, check=True)
            subprocess.run(chgmod_command, shell=True, check=True)
            print(f"Sent setup script to {host} and made it executable")
        except subprocess.CalledProcessError as e:
            print(f"Failed to send script to {host}: {e}")