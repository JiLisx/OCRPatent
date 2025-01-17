import os
import shutil
import csv
import re
from collections import defaultdict
from tqdm import tqdm


# Function to clean and normalize file names
def clean_filename(filename):
    clean_regex = re.compile(r'\.pdf$', re.IGNORECASE)
    clean_name = clean_regex.sub('', filename).strip().upper()  # 去除扩展名并转换为大写
    return clean_name


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
    delete_dir_name = "delete"

    with tqdm(total=None, desc="Scanning PDF files", unit="file") as pbar:
        for root_path in root_paths:
            for dirpath, dirs, filenames in os.walk(root_path, topdown=True):
                dirs[:] = [d for d in dirs if d.lower() != delete_dir_name.lower()]

                for filename in filenames:
                    if filename.lower().endswith('.pdf'):
                        clean_file = clean_filename(filename)
                        downloaded_pdfs.add(clean_file)
                        duplicate_paths[clean_file].append(os.path.join(dirpath, filename))
                        pbar.update(1)
                    else:
                        non_pdfs.append(os.path.join(dirpath, filename))

    print(f"Total unique PDF files downloaded: {len(downloaded_pdfs)}")
    return downloaded_pdfs, duplicate_paths, non_pdfs


def write_reports(grant_pats, downloaded_pdfs, duplicate_paths, output_dir):
    missing_pdfs = grant_pats - downloaded_pdfs
    extra_pdfs = downloaded_pdfs - grant_pats
    duplicates = {pdf: paths for pdf, paths in duplicate_paths.items() if len(paths) > 1}

    # Write missing, extra and duplicate reports
    def write_list_to_file(file_path, items):
        with open(file_path, 'w') as file:
            for item in sorted(items):
                file.write(item + "\n")

    write_list_to_file(os.path.join(output_dir, "missing_pdfs2406.txt"), missing_pdfs)
    write_list_to_file(os.path.join(output_dir, "extra_pdfs2406.txt"), extra_pdfs)

    with open(os.path.join(output_dir, "duplicate_pdfs2406.txt"), 'w') as file:
        for pdf, paths in sorted(duplicates.items()):
            line = f"{pdf}, {len(paths)}, " + ", ".join(str(path) for path in paths)
            file.write(line + "\n")

    return missing_pdfs, extra_pdfs, duplicates


def determine_files_to_delete(duplicates):
    files_to_keep = {}
    files_to_delete = []

    for pdf, paths in duplicates.items():
        paths_with_mtime = [(path, os.path.getmtime(path)) for path in paths]
        paths_with_mtime.sort(key=lambda x: x[1], reverse=True)

        if paths_with_mtime:
            keep_path = paths_with_mtime[0][0]
            files_to_keep[pdf] = keep_path
            files_to_delete.extend([path for path, _ in paths_with_mtime[1:]])

    return files_to_keep, files_to_delete


def move_files_to_delete(files_to_delete, delete_dir):
    log_entries = []
    os.makedirs(delete_dir, exist_ok=True)

    for file_path in tqdm(files_to_delete, desc="Moving Files to Delete", unit="file"):
        try:
            relative_path = os.path.relpath(file_path, root_paths[0])
            destination_path = os.path.join(delete_dir, relative_path)
            destination_dir = os.path.dirname(destination_path)
            os.makedirs(destination_dir, exist_ok=True)
            shutil.move(file_path, destination_path)
            log_entries.append(f"Moved duplicate for deletion: {file_path} -> {destination_path}\n")
        except Exception as e:
            log_entries.append(f"Error moving {file_path}: {e}\n")

    return log_entries


def move_pdfs_and_cleanup(files_to_keep, root_paths, log_file_path):
    log_entries = []
    error_files = []

    for pdf, file_path in tqdm(files_to_keep.items(), desc="Processing PDFs", unit="file"):
        try:
            # Adjusted regex: match 'CN' + any digit sequence
            match = re.match(r'(CN)(\d+)([A-Z]?)', pdf)
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
                    subfolder_name = f"{folder_prefix}{file_number[:5]}"  # First 5 digits of the number
                    destination_folder = os.path.join(root_paths[0], folder_name, subfolder_name)
                else:
                    # Invalid number length, move to CN000
                    destination_folder = os.path.join(root_paths[0], "CN000")

                # Create the destination folder if it doesn't exist
                os.makedirs(destination_folder, exist_ok=True)

                # Ensure the file keeps the .pdf extension
                destination_path = os.path.join(destination_folder, pdf + ".pdf")
                shutil.move(file_path, destination_path)
                log_entries.append(f"Moved: {pdf} -> {destination_folder}\n")
            else:
                # If regex match fails, move to CN000
                destination_folder = os.path.join(root_paths[0], "CN000")
                os.makedirs(destination_folder, exist_ok=True)

                # Ensure the file keeps the .pdf extension
                destination_path = os.path.join(destination_folder, pdf + ".pdf")
                shutil.move(file_path, destination_path)
                log_entries.append(f"Moved (unknown format): {pdf} -> {destination_folder}\n")

        except Exception as e:
            error_files.append((pdf, str(e)))
            log_entries.append(f"Error moving {pdf}: {e}\n")

    # Writing logs to the specified log file
    with open(log_file_path, 'w') as log_file:
        log_file.writelines(log_entries)

    if error_files:
        print(f"Some files could not be moved. Details are in {log_file_path}")
    else:
        print(f"All files have been processed and moved successfully.")



if __name__ == "__main__":
    root_paths = ["/Volumes/main/project/npl/check/pdf"]
    output_dir = root_paths[0]
    grant_file = "/Volumes/main/project/npl/check/grant.txt"

    grant_pats = read_patents(grant_file)

    # Get all downloaded PDFs, duplicate PDFs, and non-PDF files
    downloaded_pdfs, duplicate_paths, non_pdfs = list_downloaded_pdfs(root_paths)

    # Write report files: including mising PDFs, extra PDFs, and duplicate PDFs
    write_reports(grant_pats, downloaded_pdfs, duplicate_paths, output_dir)

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

    # Get the list of files to keep and delete
    files_to_keep, files_to_delete = determine_files_to_delete(duplicate_paths)

    # Move files to delete
    delete_dir = os.path.join(root_paths[0], "delete")
    log_file_path = os.path.join(root_paths[0], "move_log.txt")
    move_files_to_delete(files_to_delete, delete_dir)

    # Move PDFs to their destination
    move_pdfs_and_cleanup(files_to_keep, root_paths, log_file_path)

    print("\nDone!")
