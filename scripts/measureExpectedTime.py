import os
import subprocess as sp
import argparse
import json

CWD = os.getcwd()

def parse_args():
    parser = argparse.ArgumentParser(description="Run PIT expected time estimation per file.")
    parser.add_argument("--pid", type=str, required=True, help="Project ID (e.g., Closure)")
    parser.add_argument("--bid", type=str, required=True, help="Bug ID (e.g., 2)")
    parser.add_argument("--num-threads", type=str, required=True, help="Number of threads to use")
    return parser.parse_args()

def read_results(src_classes, perFileLog_dir):
    result = {}
    for src_class in src_classes:
        # lets read log
        log_file = os.path.join(perFileLog_dir, f"{src_class}-log/expected-time-exec.log")

        result[src_class] = {}
        check = False
        with open(log_file, "r") as f:
            log_contents = f.readlines()
            for line in log_contents:
                if "=== Time Estimation Results ===" in line:
                    check = True
                
                if not check:
                    continue

                if "Number of failing tests:" in line:
                    result[src_class]["failing_tests"] = int(line.split(":")[-1].strip())
                elif "Number of passing tests:" in line:
                    result[src_class]["passing_tests"] = int(line.split(":")[-1].strip())
                elif "Lines covered by failing tests:" in line:
                    result[src_class]["lines_covered_by_failing_tests"] = int(line.split(":")[-1].strip())
                elif "Number of mutations after filter:" in line:
                    result[src_class]["mutations_after_filter"] = int(line.split(":")[-1].strip())
                elif "Lines covered by passing tests:" in line:
                    result[src_class]["lines_covered_by_passing_tests"] = int(line.split(":")[-1].strip())
                elif "Estimated time with overhead (15%):" in line: # Estimated time with overhead (15%): 1.8 minutes
                    result[src_class]["estimated_time"] = float(line.split(":")[-1].strip().split(" ")[0])

    return result

def execute_perFile_expected_time(PID, BID, NUM_THREADS, src_class):
    # 1. execute perFile_expected_time.sh <PID> <BID>
    perFile_expected_time_script = os.path.join(CWD, "perFile_expected_time.sh")
    prepare_cmd = f"{perFile_expected_time_script} {PID} {BID} {NUM_THREADS} {src_class}"
    sp.run(prepare_cmd, shell=True)

def main():
    args = parse_args()
    PID = args.pid
    BID = args.bid
    NUM_THREADS = args.num_threads

    pid_dir = f"/ssd_home/yangheechan/defects4j/{PID}"
    out_dir = f"{pid_dir}/out_dir"
    subjectInfo_dir = f"{out_dir}/{PID}-{BID}b-result/subjectInfo"


    # 1. read src_classes.txt
    src_classes_text = os.path.join(subjectInfo_dir, "src_classes.txt")
    with open(src_classes_text, "r") as f:
        src_classes = f.read().strip().split(",")

    # 2. execute perFile_expected_time.sh <PID> <BID> <NUM_THREADS> <src_class>
    for src_class in src_classes:
        execute_perFile_expected_time(PID, BID, NUM_THREADS, src_class.strip())


    # 3. read results
    perFileLog_dir = f"{out_dir}/{PID}-{BID}b-result/perFileLog"
    result = read_results(src_classes, perFileLog_dir)
    expected_time_results_json = os.path.join(subjectInfo_dir, "expected_time_results.json")
    with open(expected_time_results_json, "w") as f:
        json.dump(result, f, indent=4)

    # 4. write using_src_classes.txt
    using_src_classes_list = [k for k, v in result.items() if v]
    using_src_classes = ",".join(using_src_classes_list)
    using_src_classes_txt = os.path.join(subjectInfo_dir, "using_src_classes.txt")
    with open(using_src_classes_txt, "w") as f:
        f.write(using_src_classes)


if __name__ == "__main__":
    main()
