import os
from tqdm import tqdm
from collections import defaultdict
import re
import shutil
import csv
def read_patents(file_path, patent_column_index=0):
    patents = set()
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) > patent_column_index:
                patent_number = row[patent_column_index].strip().upper()  # Ensure consistency
                patents.add(patent_number)
    print(f"Total granted patents read: {len(patents)}")
    return patents

def list_downloaded_pdfs(root_paths):
    downloaded_pdfs = set()
    duplicate_paths = defaultdict(list)
    non_pdfs = []

    # 预编译正则表达式，用于移除 '-p920mint'、'*' 和 '.'
    clean_regex = re.compile(r'\.pdf$', re.IGNORECASE)

    delete_dir_name = "delete"

    # 初始化进度条，没有预设总数
    with tqdm(total=None, desc="Scanning PDF files", unit="file") as pbar:
        for root_path in root_paths:
       	    for dirpath, dirs, filenames in os.walk(root_path, topdown=True):
                dirs[:] = [d for d in dirs if d.lower() != delete_dir_name.lower()]
                
                for filename in filenames:
                    if filename.lower().endswith('.pdf'):
                        # 使用正则表达式清理文件名
                        clean_filename = clean_regex.sub('', filename)
                        clean_filename = clean_filename.strip().upper()  # 去除首尾空格并转换为大写
                        downloaded_pdfs.add(clean_filename)
                        duplicate_paths[clean_filename].append(os.path.join(dirpath, filename))
                        pbar.update(1)
                    else:
                        non_pdfs.append(os.path.join(dirpath,filename))

    print(f"Total unique PDF files downloaded: {len(downloaded_pdfs)}")
    return downloaded_pdfs, duplicate_paths, non_pdfs


def write_reports(grant_pats, downloaded_pdfs, duplicate_paths, output_dir):
    missing_pdfs = grant_pats - downloaded_pdfs
    extra_pdfs = downloaded_pdfs - grant_pats
    duplicates = {pdf: paths for pdf, paths in duplicate_paths.items() if len(paths) > 1}

    # 写入缺失的 PDF 列表
    missing_list_file = os.path.join(output_dir, "missing_pdfs2406.txt")
    with open(missing_list_file, 'w') as file:
        for pdf in sorted(missing_pdfs):
            file.write(pdf + "\n")
    print(f"Missing PDFs have been written to: {missing_list_file}")

    # 写入多余的 PDF 列表
    extra_list_file = os.path.join(output_dir, "extra_pdfs2406.txt")
    with open(extra_list_file, 'w') as file:
        for pdf in sorted(extra_pdfs):
            file.write(pdf + "\n")
    print(f"Extra PDFs have been written to: {extra_list_file}")

    # 写入重复的 PDF 列表及其路径
    duplicate_list_file = os.path.join(output_dir, "duplicate_pdfs2406.txt")
    with open(duplicate_list_file, 'w') as file:
        for pdf, paths in sorted(duplicates.items()):
            line = f"{pdf}, {len(paths)}, " + ", ".join(paths)
            file.write(line + "\n")
    print(f"Duplicate PDFs and their paths have been written to: {duplicate_list_file}")

    return missing_pdfs, extra_pdfs, duplicates

def determine_files_to_delete(duplicates):
    files_to_keep = {}
    files_to_delete = []

    for pdf, paths in duplicates.items():
        # 获取每个文件的修改时间
        paths_with_mtime = []
        for path in paths:
            try:
                mtime = os.path.getmtime(path)
                paths_with_mtime.append((path, mtime))
            except OSError as e:
                print(f"Error accessing file {path}: {e}")

        if not paths_with_mtime:
            continue

        # 按修改时间排序，保留最新的文件
        paths_with_mtime.sort(key=lambda x: x[1], reverse=True)
        keep_path, keep_mtime = paths_with_mtime[0]
        files_to_keep[pdf] = keep_path

        # 其他文件标记为删除
        for path, _ in paths_with_mtime[1:]:
            files_to_delete.append(path)

    return files_to_keep, files_to_delete


def delete_files(files_to_delete, log_file_path, root_paths):
    """
    将需要删除的文件移动到 'delete' 文件夹，并记录操作日志。
    
    参数:
    - files_to_delete: 要移动的文件路径列表。
    - log_file_path: 操作日志文件路径。
    - root_paths: 根目录列表，用于计算相对路径。
    """
    deleted_files = []
    error_files = []
    log_entries = []
    
    # 定义 'delete' 文件夹路径
    delete_dir = os.path.join(os.path.dirname(log_file_path), "delete")
    
    # 创建 'delete' 文件夹，如果不存在
    os.makedirs(delete_dir, exist_ok=True)
    
    for file in tqdm(files_to_delete, desc="Moving duplicate PDF files to 'delete' folder", unit="file"):
        try:
            # 计算文件相对于其根目录的相对路径
            relative_path = None
            for root_path in root_paths:
                if file.startswith(root_path):
                    relative_path = os.path.relpath(file, root_path)
                    break
            if relative_path is None:
                # 如果无法找到相对路径，直接使用文件名
                relative_path = os.path.basename(file)
            
            # 定义目标路径
            destination_path = os.path.join(delete_dir, relative_path)
            
            # 确保目标子目录存在
            destination_dir = os.path.dirname(destination_path)
            os.makedirs(destination_dir, exist_ok=True)
            
            # 移动文件
            shutil.move(file, destination_path)
            deleted_files.append(file)
            log_entries.append(f"Moved: {file} -> {destination_path}\n")
        except Exception as e:
            error_files.append((file, str(e)))
            log_entries.append(f"Error moving {file}: {e}\n")
    
    # 批量写入日志
    with open(log_file_path, 'w') as log_file:
        log_file.writelines(log_entries)

    # print(f"Moved files have been logged to: {log_file_path}")

    if error_files:
        print(f"Some files could not be moved. Details are in {log_file_path}")
    else:
        print("All duplicate files have been successfully moved to the 'delete' folder.")


def write_files_to_delete(files_to_delete, file_path):
    with open(file_path, 'w') as file:
        for path in files_to_delete:
            file.write(path + "\n")
    print(f"List of files to delete has been written to: {file_path}")


if __name__ == "__main__":
     # 定义需要遍历的根目录列表
    root_paths = ["/data/home/jdang/SIPO_PDF_B/pdf"]
    output_dir = root_paths[0]
    grant_file = "/data/home/jdang/SIPO_PDF_B/grant2406.csv"
    missing_list_file = os.path.join(root_paths[0], "missing_pdfs2406.txt")
    extra_list_file = os.path.join(root_paths[0], "extra_pdfs2406.txt")
    duplicate_list_file = os.path.join(root_paths[0], "duplicate_pdfs2406.txt")
    files_to_delete_list_file = os.path.join(root_paths[0], "files_to_delete2406.txt")
    deletion_log_file = os.path.join(root_paths[0], "deletion_log2406.txt")


    grant_pats = read_patents(grant_file)
    downloaded_pdfs, duplicate_paths, non_pdfs = list_downloaded_pdfs(root_paths)

    # 定义下载的 PDF 文件列表输出路径
    downloaded_list_file = os.path.join(output_dir, "downloaded_pdfs2406.txt")

    # 定义非 PDF 文件列表输出路径
    non_pdfs_list_file = os.path.join(output_dir, "non_pdfs2406.txt")

    # 将 downloaded_pdfs 写入文件
    with open(downloaded_list_file, 'w') as f:
        for pdf in sorted(downloaded_pdfs):
            f.write(pdf + "\n")
    print(f"Downloaded PDFs have been written to: {downloaded_list_file}")

    with open(non_pdfs_list_file, 'w') as f:
        for path in sorted(non_pdfs):
            f.write(path + "\n")
    print(f"Non-PDF files have been written to: {non_pdfs_list_file}")


    missing_pdfs, extra_pdfs, duplicates = write_reports(grant_pats, downloaded_pdfs, duplicate_paths, output_dir)

    if not missing_pdfs:
        print("No missing PDFs found.")
    else:
        print(f"Missing pdf has been written to {missing_list_file}")

    if not extra_pdfs:
        print("No extra PDFs found.")
    else:
        print(f"Extra PDF has been written to {extra_list_file}")
    
    if not duplicates:
        print("No duplicate PDFs found.")
    else:
        print(f"Duplicate PDFs have been written to {duplicate_list_file}")

        # 确定要保留和删除的文件
        files_to_keep, files_to_delete = determine_files_to_delete(duplicates)

        # 将要删除的文件写入文件
        write_files_to_delete(files_to_delete, files_to_delete_list_file)

        # 列出将要删除的文件
        print("\n以下是将要删除的重复旧文件：")
        for file in files_to_delete:
            print(file)

        # 直接删除文件，并记录删除的文件路径
        delete_files(files_to_delete, deletion_log_file, root_paths)

    print("\nDone!")
