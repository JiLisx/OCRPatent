import os
from tqdm import tqdm
from collections import defaultdict

def read_patents(file_path):
    with open(file_path, 'r') as file:
        patents = set(line.strip() for line in file.readlines())
    print(f"Total granted patents read: {len(patents)}")
    return patents

def list_downloaded_pdfs(root_paths):
    downloaded_pdfs = set()
    duplicate_paths = defaultdict(list)
    total_files = 0

    if exclude_paths is None:
        exclude_paths = []

    # 计算 PDF 文件总数，同时排除指定的文件夹
    for root_path in root_paths:
        for dirpath, _, filenames in os.walk(root_path):
            total_files += len([f for f in filenames if f.endswith('.pdf')])
    print(f"Total patent PDF files found: {total_files}")

    # 使用进度条扫描 PDF 文件
    with tqdm(total=total_files, desc="Scanning PDF files") as pbar:
        for root_path in root_paths:
            for dirpath, _, filenames in os.walk(root_path):
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

def delete_files(files_to_delete):
    for file in tqdm(files_to_delete, desc="Deleting duplicate PDF files"):
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except OSError as e:
            print(f"Error deleting file {file}: {e}")

def write_files_to_delete(files_to_delete, file_path):
    with open(file_path, 'w') as file:
        for path in files_to_delete:
            file.write(path + "\n")
    print(f"List of files to delete has been written to: {file_path}")


if __name__ == "__main__":
     # 定义需要遍历的根目录列表
    root_paths = "/data/home/jdang/SIPO_PDF_B/pdf"

    grant_file = "/data/home/jdang/SIPO_PDF_B/grant2406.csv"
    missing_list_file = os.path.join(root_paths[0], "missing_pdfs2406.txt")
    extra_list_file = os.path.join(root_paths[0], "extra_pdfs2406.txt")
    duplicate_list_file = os.path.join(root_paths[0], "duplicate_pdfs2406.txt")
    files_to_delete_list_file = os.path.join(root_paths[0], "files_to_delete2406.txt")
    
    grant_pats = read_patents(grant_file)
    downloaded_pdfs, duplicate_paths = list_downloaded_pdfs(root_paths)
    missing_pdfs, extra_pdfs, duplicates = write_reports(grant_pats, downloaded_pdfs, duplicate_paths, output_dir)


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

        # 确定要保留和删除的文件
        files_to_keep, files_to_delete = determine_files_to_delete(duplicates)

        # 将要删除的文件写入文件
        write_files_to_delete(files_to_delete, files_to_delete_list_file)

        # 列出将要删除的文件
        print("\n以下是将要删除的重复旧文件：")
        for file in files_to_delete:
            print(file)

        # 提示用户进行删除操作
        user_input = input("\n是否删除以上列出的重复旧文件？输入 'y' 确认删除，输入任何其他键取消： ").strip().lower()
        if user_input == 'y':
            # 删除文件
            delete_files(files_to_delete)
            print("删除操作已完成。")
        else:
            print("删除操作已取消。要删除文件，请重新运行脚本并输入 'y'。")

    print("\n所有操作已完成。")
