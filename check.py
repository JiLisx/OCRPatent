import os
from tqdm import tqdm
import shutil
import csv
import re
from collections import defaultdict 

# Function to read patents from a CSV file
def read_patents(file_path, patent_column_index=0):
    patents = set()
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) > patent_column_index:
                patent_number = row[patent_column_index].strip().upper()
                patents.add(patent_number)
    print(f"Total granted patents read: {len(patents)}")
    return patents

# Function to list all the downloaded PDF files and handle duplicates
def list_downloaded_pdfs(root_paths):
    downloaded_pdfs = set()
    duplicate_paths = defaultdict(list) 
    non_pdfs = []

    clean_regex = re.compile(r'\.pdf$', re.IGNORECASE)

    delete_dir_name = "delete"

    with tqdm(total=None, desc="Scanning PDF files", unit="file") as pbar:
        for root_path in root_paths:
       	    for dirpath, dirs, filenames in os.walk(root_path, topdown=True):
                dirs[:] = [d for d in dirs if d.lower() != delete_dir_name.lower()]
                
                for filename in filenames:
                    if filename.lower().endswith('.pdf'):
                        clean_filename = clean_regex.sub('', filename)
                        clean_filename = clean_filename.strip().upper()  # 去除首尾空格并转换为大写
                        downloaded_pdfs.add(clean_filename)
                        duplicate_paths[clean_filename].append(os.path.join(dirpath, filename))
                        pbar.update(1)
                    else:
                        non_pdfs.append(os.path.join(dirpath,filename))

    print(f"Total unique PDF files downloaded: {len(downloaded_pdfs)}")
    print(f"Duplicate PDFs files downloaded: {len(duplicate_paths)}")

    return downloaded_pdfs, duplicate_paths, non_pdfs


def write_reports(grant_pats, downloaded_pdfs, duplicate_paths, output_dir):
    missing_pdfs = grant_pats - downloaded_pdfs
    extra_pdfs = downloaded_pdfs - grant_pats
    duplicates = {pdf: paths for pdf, paths in duplicate_paths.items() if len(paths) > 1}

    # Missing PDFs
    missing_list_file = os.path.join(output_dir, "missing_pdfs2406.txt")
    with open(missing_list_file, 'w') as file:
        for pdf in sorted(missing_pdfs):
            file.write(pdf + "\n")

    # Extra PDFs
    extra_list_file = os.path.join(output_dir, "extra_pdfs2406.txt")
    with open(extra_list_file, 'w') as file:
        for pdf in sorted(extra_pdfs):
            file.write(pdf + "\n")

    # Duplicate PDFs
    duplicate_list_file = os.path.join(output_dir, "duplicate_pdfs2406.txt")
    with open(duplicate_list_file, 'w') as file:
        for pdf, paths in sorted(duplicates.items()):
            line = f"{pdf}, {len(paths)}, " + ", ".join(paths)
            file.write(line + "\n")

    return missing_pdfs, extra_pdfs, duplicates


def determine_files_to_delete(duplicates):
    files_to_keep = {}
    files_to_delete = []

    for pdf, paths in duplicates.items():
        # Sort by modification time, keep the latest file
        paths_with_mtime = []
        for path in paths:
            try:
                mtime = os.path.getmtime(path)
                paths_with_mtime.append((path, mtime))
            except OSError as e:
                print(f"Error accessing file {path}: {e}")

        if not paths_with_mtime:
            continue

        # Sort by modification time, keep the latest file
        paths_with_mtime.sort(key=lambda x: x[1], reverse=True)
        keep_path, keep_mtime = paths_with_mtime[0]
        files_to_keep[pdf] = keep_path

        # Mark the other files for deletion
        for path, _ in paths_with_mtime[1:]:
            files_to_delete.append(path)

    return files_to_keep, files_to_delete


def move_pdfs_and_cleanup(downloaded_pdfs, root_paths, delete_dir, log_file_path, duplicate_paths):
    """
    Handle PDF files:
    - Move duplicate files to the delete folder.
    - Files starting with CN followed by 9, 8, or 7 digits should be moved to corresponding folders based on the rules.
    - If the file name doesn't match any rule, move it to the CN000 folder.
    
    Parameters:
    - downloaded_pdfs: List of downloaded PDF files.
    - root_paths: List of root directory paths.
    - delete_dir: Path to the directory for duplicate files.
    - log_file_path: Path to the operation log file.
    - duplicate_paths: Dictionary containing duplicate file paths.
    """

    log_entries = []
    error_files = []
    deleted_files = []
    
    os.makedirs(delete_dir, exist_ok=True)  

    for pdf in tqdm(downloaded_pdfs, desc="Processing PDFs", unit="file"):
        try:
            # Check if the file is a duplicate
            if pdf in duplicate_paths:
                # Move the duplicate file to the delete folder
                for duplicate_path in duplicate_paths[pdf]:
                    relative_path = os.path.relpath(duplicate_path, root_paths[0])
                    destination_path = os.path.join(delete_dir, relative_path)
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True) 
                    shutil.move(duplicate_path, destination_path)  
                    log_entries.append(f"Moved duplicate: {duplicate_path} -> {destination_path}\n")
                continue 

            # Check the file name pattern
            match = re.match(r'(CN\d{3})(\d{5})([A-Z]?)', pdf)  # Handle 9-digit, 8-digit, 7-digit cases

            if match:

                folder_prefix = match.group(1) 
                file_number = match.group(2)  
                file_suffix = match.group(3)  

                if len(file_number) == 5:   # 9-digit case
                    folder_name = f"{folder_prefix}{file_number[:2]}"  
                    subfolder_name = f"{folder_prefix}{file_number[:5]}"  
                elif len(file_number) == 7:  # 7-digit case
                    file_number = f"00{file_number}"
                    folder_name = f"{folder_prefix}{file_number[:2]}"
                    subfolder_name = f"{folder_prefix}{file_number[:5]}"
                elif len(file_number) == 8:  # 8-digit case
                    file_number = f"0{file_number}"
                    folder_name = f"{folder_prefix}{file_number[:2]}"
                    subfolder_name = f"{folder_prefix}{file_number[:5]}"

                destination_folder = os.path.join(root_paths[0], folder_name, subfolder_name)
                os.makedirs(destination_folder, exist_ok=True)  
                source_path = os.path.join(root_paths[0], pdf)
                destination_path = os.path.join(destination_folder, pdf)
                shutil.move(source_path, destination_path) 

                log_entries.append(f"Moved: {pdf} -> {destination_folder}\n")
            else:
                # If the file name doesn't match the above rules, move it to CN000 folder
                destination_folder = os.path.join(root_paths[0], "CN000")
                os.makedirs(destination_folder, exist_ok=True)
                source_path = os.path.join(root_paths[0], pdf)
                destination_path = os.path.join(destination_folder, pdf)
                shutil.move(source_path, destination_path) 
                log_entries.append(f"Moved (unknown format): {pdf} -> {destination_folder}\n")

        except Exception as e:
            error_files.append((pdf, str(e)))
            log_entries.append(f"Error moving {pdf}: {e}\n")

    # Write the log
    with open(log_file_path, 'w') as log_file:
        log_file.writelines(log_entries)

    # Output processing result
    if error_files:
        print(f"Some files could not be moved. Details are in {log_file_path}")
    else:
        print(f"All files have been processed and moved successfully.")


if __name__ == "__main__":

    root_paths = ["/data/home/jdang/SIPO_PDF_B/pdf"]
    output_dir = root_paths[0]
    grant_file = "/data/home/jdang/SIPO_PDF_B/grant2406.csv"

    grant_pats = read_patents(grant_file)
    
    # Get all downloaded PDFs, duplicate PDFs, and non-PDF files
    downloaded_pdfs, duplicate_paths, non_pdfs = list_downloaded_pdfs(root_paths)

    # Write report files: including missing PDFs, extra PDFs, and duplicate PDFs
    write_reports(grant_pats, downloaded_pdfs, duplicate_paths, output_dir)

    # Get the list of files to keep and delete
    files_to_keep, files_to_delete = determine_files_to_delete(duplicate_paths)

    # Write the list of downloaded PDFs and non-PDF files to files
    downloaded_list_file = os.path.join(output_dir, "downloaded_pdfs2406.txt")
    non_pdfs_list_file = os.path.join(output_dir, "non_pdfs2406.txt")

    with open(downloaded_list_file, 'w') as f:
        for pdf in sorted(downloaded_pdfs):
            f.write(pdf + "\n")
    print(f"Downloaded PDFs have been written to: {downloaded_list_file}")

    with open(non_pdfs_list_file, 'w') as f:
        for path in sorted(non_pdfs):
            f.write(path + "\n")
    print(f"Non-PDF files have been written to: {non_pdfs_list_file}")
    
    # delete duplicates files
    delete_dir = os.path.join(root_paths[0], "delete")
    log_file_path = os.path.join(root_paths[0], "move_log.txt")
    move_pdfs_and_cleanup(downloaded_pdfs, root_paths, delete_dir, log_file_path, duplicate_paths)

    print("\nDone!")

