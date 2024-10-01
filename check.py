import os
from tqdm import tqdm
from collections import defaultdict

def read_patents(file_path):
    with open(file_path, 'r') as file:
        patents = set(line.strip() for line in file.readlines())
    print(f"Total granted patents read: {len(patents)}")
    return patents

def list_downloaded_pdfs(root_paths, exclude_paths=None):
    downloaded_pdfs = set()
    duplicate_paths = defaultdict(list)
    total_files = 0

    if exclude_paths is None:
        exclude_paths = []

    # 计算 PDF 文件总数，同时排除指定的文件夹
    for root_path in root_paths:
        for dirpath, _, filenames in os.walk(root_path):
            if any(exclude in dirpath for exclude in exclude_paths):
                continue  # Skip excluded paths
            total_files += len([f for f in filenames if f.endswith('.pdf')])
    print(f"Total patent PDF files found: {total_files}")

    # 使用进度条扫描 PDF 文件
    with tqdm(total=total_files, desc="Scanning PDF files") as pbar:
        for root_path in root_paths:
            for dirpath, _, filenames in os.walk(root_path):
                if any(exclude in dirpath for exclude in exclude_paths):
                    continue  # Skip excluded paths
                for filename in filenames:
                    if filename.endswith('.pdf'):
                        # 去掉文件名中的特殊字符
                        clean_filename = filename.replace('*', '').replace('.pdf', '').replace('-p920mint', '')
                        clean_filename = clean_filename.strip().upper()  # 统一转换为大写并去除首尾空格
                        downloaded_pdfs.add(clean_filename)
                        duplicate_paths[clean_filename].append(os.path.join(dirpath, filename))
                    pbar.update(1)

    print(f"Total PDF files downloaded: {len(downloaded_pdfs)}")
    return downloaded_pdfs, duplicate_paths


def find_missing_pdfs(grant_pats, downloaded_pdfs):
    missing_pdfs = grant_pats - downloaded_pdfs
    print(f"Patents found in the grant file but missing in the download files: {len(missing_pdfs)}")
    return missing_pdfs

def find_extra_pdfs(downloaded_pdfs, grant_pats):
    extra_pdfs = downloaded_pdfs - grant_pats
    print(f"Extra PDF files found in the download directory but not in the grant file: {len(extra_pdfs)}")
    return extra_pdfs

def find_duplicate_pdfs(duplicate_paths):
    duplicates = {pdf: paths for pdf, paths in duplicate_paths.items() if len(paths) > 1}
    print(f"Total duplicate PDFs that has been downloaded found: {len(duplicates)}")
    return duplicates


def write_missing_pdfs(missing_pdfs, file_path):
    with open(file_path, 'w') as file:
        for pdf in sorted(missing_pdfs):
            file.write(pdf + "\n")

def write_extra_pdfs(extra_pdfs, file_path):
    with open(file_path, 'w') as file:
        for pdf in sorted(extra_pdfs):
            file.write(pdf + "\n")

def write_duplicate_pdfs(duplicates, file_path):
    with open(file_path, 'w') as file:
        for pdf, paths in sorted(duplicates.items()):
            line = f"{pdf}, {len(paths)}, " + ", ".join(paths)
            file.write(line + "\n")
    print(f"Duplicate PDFs and their paths written to: {file_path}")

    
if __name__ == "__main__":
     # 定义需要遍历的根目录列表
    root_paths = [
        "/data/home/jdang/SIPO_PDF_B",
        "/data/home/liji/dload/dload2023"
    ]
    # 定义需要排除的目录
    exclude_paths = [
        "/data/home/liji/dload/dload2023/CN123A",
        "/data/home/liji/dload/dload2023/CN122"
    ]
    grant_file = os.path.join(root_paths[0], "grant_pnr_all2406.txt")
    missing_list_file = os.path.join(root_paths[0], "missing_pdfs2406.txt")
    extra_list_file = os.path.join(root_paths[0], "extra_pdfs2406.txt")
    duplicate_list_file = os.path.join(root_paths[0], "duplicate_pdfs2406.txt")

    grant_pats = read_patents(grant_file)
    downloaded_pdfs, duplicate_paths = list_downloaded_pdfs(root_paths, exclude_paths)
    missing_pdfs = find_missing_pdfs(grant_pats, downloaded_pdfs)
    extra_pdfs = find_extra_pdfs(downloaded_pdfs, grant_pats)
    duplicates = find_duplicate_pdfs(duplicate_paths)

    # 写入缺失的 PDF 列表
    write_missing_pdfs(missing_pdfs, missing_list_file)

    # 写入多余的 PDF 列表
    write_extra_pdfs(extra_pdfs, extra_list_file)

    # 写入重复的 PDF 列表及其路径
    write_duplicate_pdfs(duplicates, duplicate_list_file)
    
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

