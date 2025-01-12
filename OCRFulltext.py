"""
 Author: Li Ji
 Date: Dec 17 2024
 OCR full text of patent description
"""

import sys
import os
import json
import re
import pytesseract
from pdf2image import convert_from_path
import multiprocessing
from tqdm import tqdm
from functools import partial
import argparse


def ocr_page(img):
    try:
        # print('ocr_image begin...')
        oem_psm_config = r'--psm 6'
        text = pytesseract.image_to_string(img, config = oem_psm_config, lang='chi_sim')
        # print('ocr_image end...')
        # print(f"OCR Result:\n{text[:500]}...\n{'-' * 40}\n")

        return text
    except Exception as e:
        raise RuntimeError(f"Error during OCR: {e}")


def extract_header(text, num_chars=50):
    """
    提取并预处理页面的页眉部分，用于识别说明书的开始和结束。
    假设页眉在页面的前 num_chars 个字符内。
    """
    # 提取前 num_chars 个字符作为页眉
    header = text[:num_chars]

    # 只保留中文、英文、数字和常见标点
    cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', header)
    # 将多个空格替换为单个空格
    cleaned_text = re.sub(r'\s+', '', cleaned_text)

    return cleaned_text.strip()

# 定义正则表达式模式，允许关键字之间有任意非字母数字字符
START_PATTERN = re.compile(r'说\s*明\s*书|Description', re.IGNORECASE)
END_PATTERN = re.compile(r'说\s*明\s*书\s*附\s*图|Drawings', re.IGNORECASE)

def process_pdf(pdf_file, folder_path, finished_pdfs, output_folder):
    # print(f'process_pdf {pdf_file} start...')
    pnr = os.path.basename(pdf_file).split('.')[0]
    if pnr in finished_pdfs:
        return None, pnr, True  # Already processed

    pdf_path = os.path.join(folder_path, pdf_file)

    try:
        images = convert_from_path(pdf_path, dpi=300)

        description_started = False
        ocr_text = []

        for i, image in enumerate(images):
            text = ocr_page(image)
            header = extract_header(text)

            # 检查是否开始说明书
            if not description_started:
                if START_PATTERN.search(header):
                    description_started = True
                    ocr_text.append(text)
                continue
            else:
                # 检查是否结束说明书
                if END_PATTERN.search(header):
                    description_started = False
                    break
                else:
                    ocr_text.append(text)

        if not ocr_text:
            print(f"No description section found in {pdf_file}.")
            return None, pnr, False

        # 合并所有文本
        full_text = ''.join(ocr_text).strip()

        # 创建结果字典
        result = {"pnr": pnr, "description": full_text}

        # 将结果保存为单个JSON文件
        """
        json_output_path = os.path.join(output_folder, f"{pnr}.json")
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        """
        return result, pnr, True  # 返回结果, pnr, 成功
    except Exception as e:
        print(f"Error processing {pdf_file}: {e}")
        return None, pnr, False  # 返回 pnr 和失败标志

def get_target_pdfs(input_pdf_list, folder_path):
    # 读取目标 PDF 文件名，仅获取第一列，分隔符为|
    with open(input_pdf_list, 'r') as f:
        target_pdfs = {line.strip().split('|')[0] + ".pdf" for line in f}

    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file in target_pdfs:
                file_path = os.path.relpath(os.path.join(root, file), folder_path)
                pdf_files.append(file_path)
    return pdf_files

def get_all_pdfs(folder_path):
    # 遍历指定目录及其子目录，获取所有 PDF 文件的相对路径。
    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                # 获取相对路径，以便后续处理
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                pdf_files.append(rel_path)
    return pdf_files

def process_pdf_folder(folder_path, output_folder, input_pdf_list=None, num_processes=10):
    """
    处理指定文件夹中的 PDF 文件。

    参数：
    - folder_path: PDF 文件所在的根目录路径
    - output_folder: 输出结果的文件夹路径
    - input_pdf_list: 可选的 pdflist.txt 文件路径
    - num_processes: 并行处理的进程数
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    finish_file = os.path.join(output_folder, "finish.txt")
    failed_file = os.path.join(output_folder, "failed.txt")
    json_file = os.path.join(output_folder, "FullText.json")

    if not os.path.exists(finish_file):
        open(finish_file, 'w').close()

    if not os.path.exists(failed_file):
        open(failed_file, 'w').close()

    with open(finish_file, 'r') as file:
        finished_pdfs = set(line.strip() for line in file.readlines())

    with open(failed_file, 'r') as file:
        failed_pdfs = set(line.strip() for line in file.readlines())

    # 获取 PDF 文件列表
    if input_pdf_list:
        pdf_files = get_target_pdfs(input_pdf_list, folder_path)
    else:
        pdf_files = get_all_pdfs(folder_path)

    # 过滤已处理的文件
    if input_pdf_list:
        # 在使用 pdflist.txt 时，finished_pdfs 应该包含 pnr，不是完整路径
        pdf_files = [pdf for pdf in pdf_files if os.path.splitext(os.path.basename(pdf))[0] not in finished_pdfs]
    else:
        pdf_files = [pdf for pdf in pdf_files if os.path.splitext(pdf)[0] not in finished_pdfs]

    print(f"总共有 {len(pdf_files)} 个未处理的 PDF 文件。")

    pool = multiprocessing.Pool(num_processes)
    process_pdf_partial = partial(process_pdf, folder_path=folder_path, finished_pdfs=finished_pdfs, output_folder=output_folder)

    results = []
    completed_count = 0

    def callback(result):
        nonlocal completed_count
        res, pnr, success = result
        if res:
            with open(json_file, 'a', encoding='utf-8') as f:
                json.dump(res, f, ensure_ascii=False)
                f.write('\n')

        if success:
            finished_pdfs.add(pnr)
            with open(finish_file, 'a') as f:
                f.write(pnr + '\n')
        else:
            failed_pdfs.add(pnr)
            with open(failed_file, 'a') as f:
                f.write(pnr + '\n')

        pbar.update(1)

    with tqdm(total=len(pdf_files), desc="Processing PDFs") as pbar:
        for pdf_file in pdf_files:
            pool.apply_async(process_pdf_partial, args=(pdf_file,), callback=callback)

        pool.close()
        pool.join()

    print("Processing completed.")
    print(f"Total PDFs processed: {len(finished_pdfs)}")
    print(f"Total PDFs failed: {len(failed_pdfs)}")


# Set the path for Tesseract and Poppler on BIGFORCE
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
poppler_path = '/usr/bin/pdftotext'
os.environ['PATH'] += os.pathsep + poppler_path
"""

# Set the path for Tesseract and Poppler on MAC
pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
poppler_path = '/usr/local/Cellar/poppler/24.04.0/bin'
os.environ['PATH'] += os.pathsep + poppler_path
"""

def main():
    parser = argparse.ArgumentParser(description='批量处理目录下的所有 PDF 文件。')
    parser.add_argument('directory', type=str, help='待处理 PDF 文件的根目录路径')
    parser.add_argument('--output', type=str, default='./ocr_results/', help='输出结果存放的文件夹路径')
    parser.add_argument('--workers', type=int, default=10, help='并行处理的进程数，默认=10')
    parser.add_argument('--pdflist', type=str, default=None, help='可选的 PDF 列表文件路径（pdflist.txt）')
    args = parser.parse_args()

    folder_path = args.directory
    output_folder = args.output
    num_processes = args.workers
    input_pdf_list = args.pdflist

    if input_pdf_list and not os.path.isfile(input_pdf_list):
        print(f"指定的 pdflist 文件不存在: {input_pdf_list}", file=sys.stderr)
        sys.exit(1)

    process_pdf_folder(folder_path, output_folder, input_pdf_list=input_pdf_list, num_processes=num_processes)

if __name__ == '__main__':
    main()

    """
使用示例   
# 处理整个目录中的所有 PDF 文件，使用默认设置
python3 Mac_OCRFulltext_parse.py /path/to/pdf/root --output ./results --workers 1
python3 /Volumes/main/project/OCRFullText/Mac_OCRFulltext_parse.py /Volumes/main/project/OCRFullText/pdftest --output ./results/ --workers 1

# 仅处理 pdflist.txt 中指定的 PDF 文件
python3 Mac_OCRFulltext_parse.py /Volumes/main/project/OCRFullText/Mac_OCRFulltext_parse.py --output ./results --workers 1 --pdflist ./pdf_list.txt

"""
