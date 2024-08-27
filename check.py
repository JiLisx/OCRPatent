import os
from tqdm import tqdm

def read_patents(file_path):
    with open(file_path, 'r') as file:
        patents = set(line.strip() for line in file.readlines())
    print(f"Total patents read: {len(patents)}")
    return patents

def list_downloaded_pdfs(root_path):
    downloaded_pdfs = set()
    total_files = 0

    # 计算 PDF 文件总数
    for dirpath, _, filenames in os.walk(root_path):
        total_files += len([f for f in filenames if f.endswith('.pdf')])
    print(f"Total PDF files found: {total_files}")

    with tqdm(total=total_files, desc="Scanning PDF files") as pbar:
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                if filename.endswith('.pdf'):
                    # 去掉文件名中的星号
                    clean_filename = filename.replace('*', '').replace('.pdf', '')
                    downloaded_pdfs.add(clean_filename)
                pbar.update(1)
    print(f"Total PDF files processed: {len(downloaded_pdfs)}")
    return downloaded_pdfs

def find_extra_pdfs(grant_pats, downloaded_pdfs):
    extra_pdfs = downloaded_pdfs - grant_pats
    print(f"Total extra PDFs: {len(extra_pdfs)}")
    return extra_pdfs

def write_missing_pdfs(missing_pdfs, file_path):
    with open(file_path, 'w') as file:
        for pdf in sorted(missing_pdfs):
            file.write(pdf + "\n")
    print(f"Extra PDFs written to: {file_path}")

if __name__ == "__main__":
    root_path = "/data/home/jdang/SIPO_PDF_B"
    grant_file = os.path.join(root_path, "grant_to2022.txt")
    extra_list_file = os.path.join(root_path, "missing_pdfs.txt")

    grant_pats = read_patents(grant_file)
    downloaded_pdfs = list_downloaded_pdfs(root_path)
    extra_pdfs = find_extra_pdfs(grant_pats, downloaded_pdfs)

    # 写入多余的 PDF 列表
    write_missing_pdfs(extra_pdfs, extra_list_file)

    if not extra_pdfs:
        print("No extra PDFs found.")
    else:
        print(f"Extra PDFs list has been written to {extra_list_file}")

