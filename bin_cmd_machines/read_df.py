#!/usr/bin/python3


from pathlib import Path
import json


file_path = Path(__file__).resolve()
cur_dir = file_path.parent
df_file = cur_dir / "df.6"

keys = ["ssd_name", "size", "used", "avail.", "used%", "mounted_on"]


def main():

  df_data = {}

  with open(df_file, "r") as fp:
    lines = fp.readlines()
    for line in lines:
      line = line.strip()
      info = line.split(" ")

      if info[-1].split(".")[-1] == "swtv":
        server_name = info[-1]
        assert server_name not in df_data
        df_data[server_name] = []

      if "nvme" in info[0].split("/")[-1] and info[-1] == "/":
        cnt = 0
        dat = {}
        for d in info:
          if d != "":
            dat[keys[cnt]] = d
            cnt += 1

        df_data[server_name].append(dat)

  print(json.dumps(df_data, indent=2))

  for server in df_data:
    json_dat = df_data[server][0]
    if float(json_dat["avail."][:-1]) < 300.0:
      print(server)
      print(json_dat)
    



if __name__ == "__main__":
  main()
