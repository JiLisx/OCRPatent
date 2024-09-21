import os
from tqdm import tqdm

def read_patents(file_path):
    with open(file_path, 'r') as file:
        patents = set(line.strip() for line in file.readlines())
    print(f"Total granted patents read: {len(patents)}")
    return patents

def list_downloaded_pdfs(root_path):
    downloaded_pdfs = set()
    total_files = 0

    # 计算 PDF 文件总数
    for root_path in root_paths:
        for dirpath, _, filenames in os.walk(root_path):
            total_files += len([f for f in filenames if f.endswith('.pdf')])
    print(f"Total patent PDF files found: {total_files}")

    with tqdm(total=total_files, desc="Scanning PDF files") as pbar:
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                if filename.endswith('.pdf'):
                    # 去掉文件名中的星号
                    clean_filename = filename.replace('*', '').replace('.pdf', '').replace('-p920mint', '')
                    downloaded_pdfs.add(clean_filename)
                pbar.update(1)
    print(f"Total PDF files processed : {len(downloaded_pdfs)}")
    return downloaded_pdfs

def find_missing_pdfs(grant_pats, downloaded_pdfs):
    extra_pdfs = grant_pats - downloaded_pdfs
    print(f"Total missing PDFs: {len(find_missing_pdfs)}")
    return extra_pdfs

def write_missing_pdfs(missing_pdfs, file_path):
    with open(file_path, 'w') as file:
        for pdf in sorted(missing_pdfs):
            file.write(pdf + "\n")
    print(f"Extra PDFs written to: {file_path}")

if __name__ == "__main__":
     # 定义需要遍历的根目录列表
    root_paths = [
        "/data/home/jdang/SIPO_PDF_B",
        "/data/home/liji/dload/dload2023"
    ]
    grant_file = os.path.join(root_paths, "grant_pnr_all2406.txt")
    extra_list_file = os.path.join(root_paths, "missing_pdfs2406.txt")

    grant_pats = read_patents(grant_file)
    downloaded_pdfs = list_downloaded_pdfs(root_path)
    extra_pdfs = find_extra_pdfs(grant_pats, downloaded_pdfs)

    # 写入多余的 PDF 列表
    write_missing_pdfs(extra_pdfs, extra_list_file)

    if not extra_pdfs:
        print("No missing PDFs found.")
    else:
        print(f"Missing PDFs list has been written to {extra_list_file}")

