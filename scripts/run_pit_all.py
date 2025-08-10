import os
import subprocess as sp
import argparse
import json

CWD = os.getcwd()

def parse_args():
    parser = argparse.ArgumentParser(description="Run PIT mutation testing per file.")
    parser.add_argument("--pid", type=str, required=True, help="Project ID (e.g., Closure)")
    parser.add_argument("--bid", type=str, required=True, help="Bug ID (e.g., 2)")
    parser.add_argument("--num-threads", type=str, required=True, help="Number of threads to use")
    return parser.parse_args()

def execute_perFile_pit(PID, BID, NUM_THREADS, src_class):
    # 1. execute perFile_pit.sh <PID> <BID>
    perFile_pit_script = os.path.join(CWD, "perFile_pit.sh")
    prepare_cmd = f"{perFile_pit_script} {PID} {BID} {NUM_THREADS} {src_class}"
    res = sp.run(prepare_cmd, shell=True)

    if res.returncode != 0:
        return 1
    return 0

def main():
    args = parse_args()
    PID = args.pid
    BID = args.bid
    NUM_THREADS = args.num_threads

    pid_dir = f"/ssd_home/yangheechan/defects4j/{PID}"
    out_dir = f"{pid_dir}/out_dir"
    subjectInfo_dir = f"{out_dir}/{PID}-{BID}b-result/subjectInfo"


    # 1. get using classes
    using_src_classes_txt = os.path.join(subjectInfo_dir, "using_src_classes.txt")
    with open(using_src_classes_txt, "r") as f:
        using_src_classes = f.read().strip().split(",")
    
    # 2. execute perFile_pit.sh <PID> <BID> <NUM_THREADS> <src_class>
    execution_results = {}
    for src_class in using_src_classes:
        src_class = src_class.strip()
        
        # 2. execute perFile_pit.sh <PID> <BID> <NUM_THREADS> <src_class>
        res = execute_perFile_pit(PID, BID, NUM_THREADS, src_class)
        if res != 0:
            execution_results[src_class] = "Error"
        else:
            execution_results[src_class] = "Success"
    
    # 3. write results to JSON
    pit_exec_results_json = os.path.join(subjectInfo_dir, "pit_execution_results.json")
    with open(pit_exec_results_json, "w") as f:
        json.dump(execution_results, f, indent=4)
    

    # 4. remove workdir
    work_dir = f"/ssd_home/yangheechan/defects4j/{PID}/{PID}-{BID}b"
    if os.path.exists(work_dir):
        sp.run(f"rm -rf {work_dir}", shell=True)
        print(f"Removed work directory: {work_dir}")
    
    # if any of execution result is "error", exit with code 1
    if "Error" in execution_results.values():
        print("Some executions failed. Exiting with code 1.")
        exit(1)
    else:
        print("All executions succeeded. Exiting with code 0.")
        exit(0)
    
if __name__ == "__main__":
    main()
