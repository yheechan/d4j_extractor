#!/usr/bin/python3


from pathlib import Path
import json


file_path = Path(__file__).resolve()
cur_dir = file_path.parent
tool_dir = cur_dir.parent
main_dir = tool_dir.parent
configs_dir = main_dir / "configs"
machines_json_file = configs_dir / "machines.json"

keys = ["ssd_name", "size", "used", "avail.", "used%", "mounted_on"]


def main():

  json_data = {}
  total_cores = 0
  with open(machines_json_file) as f:
    json_data = json.load(f)
    for server in json_data:
      total_cores += json_data[server]["cores"]
      print(f"{server}: {json_data[server]['cores']} cores")
  print(f"Total cores: {total_cores}")




if __name__ == "__main__":
  main()
