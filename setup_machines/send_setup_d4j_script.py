
# write me a script the sends ../scripts/setup_d4j.sh to machines listed in ~/.hosts/mbfl_servers
# send the script to homedirectory of the user on the remote machine
import os

# just use scp
import subprocess

USERNAME = 'yangheechan'
PASSWORD = 'yang1234!'
HOME_DIR = '/home/yangheechan'


def send_setup_script():
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
        # also change the file to executable chmod +x setup_d4j.sh
        chgmod_command = f'ssh {USERNAME}@{host} "chmod +x {HOME_DIR}/setup_d4j.sh"'
        try:
            subprocess.run(command, shell=True, check=True)
            subprocess.run(chgmod_command, shell=True, check=True)
            print(f"Sent setup script to {host} and made it executable")
        except subprocess.CalledProcessError as e:
            print(f"Failed to send script to {host}: {e}")

if __name__ == "__main__":
    send_setup_script()
    print("Setup script sent to all specified machines.")