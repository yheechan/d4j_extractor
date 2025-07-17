import os
import json



if __name__ == "__main__":
    # Get the current working directory
    current_dir = os.getcwd()
    
    baseline_dir = os.path.join(current_dir, "baselineTestResults")
    if not os.path.exists(baseline_dir):
        print(f"Baseline directory '{baseline_dir}' does not exist.")
        exit(1)

    # Get the list of files in the baseline directory
    files = os.listdir(baseline_dir)
    if not files:
        print("No files found in the baseline directory.")
        exit(1)

    # Initialize a dictionary to hold the results
    results = {}
    for file in files:
        file_path = os.path.join(baseline_dir, file)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    results[file] = data
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {file}: {e}")
    
    # Calculate the total time "test_info": "execution_time_ms"
    total_time = 0
    for file, data in results.items():
        if "test_info" in data and "execution_time_ms" in data["test_info"]:
            total_time += data["test_info"]["execution_time_ms"]
            print(f"File: {file}, Execution Time: {data['test_info']['execution_time_ms']} ms")
    print(f"Total execution time across all tests: {total_time} ms")
