#!/usr/bin/env python3
import os
import json
import re
import glob

# Define input and output directories
# 定义输入和输出目录
ipt_dir = "/data/home/jdang/SIPO_PDF_B/results_frontpage/"
opt_dir = "/data/home/jdang/SIPO_PDF_B/results_frontpage_organized"
second_list_file = "/data/home/jdang/SIPO_PDF_B/results_frontpage/second.txt"

# Ensure the output directory exists
os.makedirs(opt_dir, exist_ok=True)

# Read the second.txt file and store the PNRs in a set for fast lookup
with open(second_list_file, 'r', encoding='utf-8') as f:
    second_pnrs = set(line.strip() for line in f)

# Function to check if the file is in NDJSON format
def is_ndjson(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                return line.startswith('{')
    return False

# Generate folder name based on the PNR
def generate_folder_name(pnr):
    match = re.match(r'(CN)(\d+)([A-Z]?)', pnr)
    if match:
        folder_prefix = match.group(1)
        file_number = match.group(2)
        file_suffix = match.group(3)

        # Check the length of the number, ensure it's 7, 8, or 9 digits
        if len(file_number) in [7, 8, 9]:
            # Ensure the file number is 9 digits, pad with zeros if necessary
            if len(file_number) < 9:
                file_number = file_number.zfill(9)

            folder_name = f"{folder_prefix}{file_number[:3]}"  # First 3 digits of the number
            return folder_name
        else:
            # Invalid number length, move to CN000
            return "CN000"  # Return "CN000" if not valid
    else:
        return "Invalid_PNR"

# Error log for tracking issues
error_log = []
folder_data = {}

# Process the JSON files and move them to the corresponding folders
for file_path in glob.glob(os.path.join(ipt_dir, '**', '*.json'), recursive=True):
    print(f"Processing file: {file_path}")

    try:
        if is_ndjson(file_path):
            # Handle NDJSON format (one JSON object per line)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            pnr = item.get("pnr", "")
                            pnr_matches = re.findall(r"CN\d+[A-Z]", pnr)
                            if not pnr_matches:
                                error_log.append(f"Invalid pnr '{pnr}' in file {file_path}")
                                continue

                            pnr_extracted = pnr_matches[0]
                            folder_name = generate_folder_name(pnr_extracted)

                            # Collect data into the respective category (second or non-second)
                            if pnr_extracted in second_pnrs:
                                folder_name = "second"
                            if folder_name not in folder_data:
                                folder_data[folder_name] = []
                            folder_data[folder_name].append(item)

                    except json.JSONDecodeError:
                        error_log.append(f"Error parsing line in NDJSON file {file_path}: {line}")
                        continue
        else:
            # Handle standard JSON format (entire file is a JSON object)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    pnr = item.get("pnr", "")
                    pnr_matches = re.findall(r"CN\d+[A-Z]", pnr)
                    if not pnr_matches:
                        error_log.append(f"Invalid pnr '{pnr}' in file {file_path}")
                        continue

                    pnr_extracted = pnr_matches[0]
                    folder_name = generate_folder_name(pnr_extracted)

                    # Collect data into the respective category (second or non-second)
                    if pnr_extracted in second_pnrs:
                        folder_name = "second"
                    if folder_name not in folder_data:
                        folder_data[folder_name] = []
                    folder_data[folder_name].append(item)

    except json.JSONDecodeError:
        error_log.append(f"Error parsing JSON in file {file_path}")
        continue

# Batch write the data to their corresponding folders
for folder_name, items in folder_data.items():
    # For second data, write to a dedicated second folder
    if folder_name == "second":
        folder_path = os.path.join(opt_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        output_file_path = os.path.join(folder_path, "second.json")
    else:
        folder_path = os.path.join(opt_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        output_file_path = os.path.join(folder_path, f"{folder_name}.json")

    # Write data to corresponding folder in NDJSON format (one JSON object per line)
    with open(output_file_path, 'a', encoding='utf-8') as out_f:
        for item in items:
            json.dump(item, out_f, ensure_ascii=False)
            out_f.write("\n")

# Output the error log if any issues occurred
if error_log:
    with open(os.path.join(opt_dir, "error_log.txt"), 'w', encoding='utf-8') as log_file:
        for entry in error_log:
            log_file.write(entry + "\n")

print(f"All JSON files have been categorized and saved to {opt_dir}")
print(f"Error log has been saved to {os.path.join(opt_dir, 'error_log.txt')}")
