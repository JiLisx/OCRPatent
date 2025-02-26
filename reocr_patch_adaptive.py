# 如果list里的pdf在目录里找不到，写出pdf到missingpdf.txt

import os
import json
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import multiprocessing
from tqdm import tqdm
from functools import partial
import sys
import cv2

def split_image(image_path):
    try:
        images = convert_from_path(image_path, dpi=400, first_page=0, last_page=1)
        img = np.array(images[0])
        img_height, img_width = img.shape[:2]
        horizontal_split_ratio = 0.5
        up_img = img[int(img_height * 0.13):int(img_height * 0.15), int(img_width * 0.6):int(img_width * 0.9)]
        down_img = img[int(img_height * 0.165):, :]
        left_img = down_img[:, :int(img_width * horizontal_split_ratio)]
        right_img = down_img[:, int(img_width * (1 - horizontal_split_ratio)):]

        # 保存切割后的图片用于调试
        # cv2.imwrite("left_image.png", left_img)
        # cv2.imwrite("right_image.png", right_img)

        return left_img, right_img
    except Exception as e:
        raise RuntimeError(f"Error during image splitting: {e}")

def split_image_adaptive(image, ratio=0.5):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    height, width = thresh.shape
    mid_row = int(height * ratio)

    upper_half = thresh[:mid_row, :]
    lower_half = thresh[mid_row:, :]

    upper_white_ratio = np.sum(upper_half == 255) / upper_half.size

    if upper_white_ratio > 0.5:
        return upper_half, lower_half
    else:
        return lower_half, upper_half

def ocr_image(img):
    try:
        # print('ocr_image begin...')
        oem_psm_config = r'--psm 6'
        text = pytesseract.image_to_string(img, config = oem_psm_config, lang='chi_sim')
        # print('ocr_image end...')
        return text
    except Exception as e:
        raise RuntimeError(f"Error during OCR: {e}")


def process_pdf(pdf_file, folder_path, finished_pdfs, output_folder):
    # print(f'process_pdf {pdf_file} start...')
    pnr = os.path.basename(pdf_file).split('.')[0]
    if pnr in finished_pdfs:
        return None, pnr, True  # Already processed

    pdf_path = os.path.join(folder_path, pdf_file)

    try:
        left_img, right_img = split_image(pdf_path)
        left_text = ocr_image(left_img)
        right_text = ocr_image(right_img)
        result = {"pnr": pnr, "left": left_text, "right": right_text}
     #  print(f'process_pdf {pdf_file} end...')

        return result, pnr, True  # Return result, pnr, and success

    except Exception as e:
        print(f"Error processing {pdf_file}: {e}")
        return None, pnr, False  # Return pnr and False to indicate failure

def get_target_pdfs(input_pdf_list, folder_path):
    with open(input_pdf_list, 'r') as f:
        target_pdfs = {line.strip().split('|')[0] + ".pdf" for line in f}

    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file in target_pdfs:
                file_path = os.path.relpath(os.path.join(root, file), folder_path)
                pdf_files.append(file_path)
    return pdf_files, target_pdfs

def process_pdf_folder(folder_path, output_folder, input_pdf_list,num_processes=10):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    finish_file = os.path.join(output_folder, "finish_reocr.txt")
    failed_file = os.path.join(output_folder, "failed_reocr.txt")
    json_file = os.path.join(output_folder, "frontpage_reocr.json")
    missing_file = os.path.join(output_folder, "missingpdf.txt") 

    if not os.path.exists(finish_file):
        open(finish_file, 'w').close()

    if not os.path.exists(failed_file):
        open(failed_file, 'w').close()

    with open(finish_file, 'r') as file:
        finished_pdfs = set(line.strip() for line in file.readlines())

    with open(failed_file, 'r') as file:
        failed_pdfs = set(line.strip() for line in file.readlines())

    pdf_files, target_pdfs = get_target_pdfs(input_pdf_list, folder_path)
    found_pnrs = set(os.path.basename(pdf).split('.')[0] for pdf in pdf_files)
    missing_pnrs = {pnr for pnr in (line.strip().split('|')[0] for line in open(input_pdf_list))} - found_pnrs

    # 写入缺失的PNR到missingpdf.txt
    with open(missing_file, 'w') as f:
        for missing_pdf in sorted(missing_pnrs):
            pnr = os.path.basename(missing_pdf).split('.')[0]
            f.write(pnr + '\n')
    print(f"Missing PNRs have been written to {missing_file}")
    
    pdf_files = [os.path.join(folder_path, pdf_file) for pdf_file in pdf_files]

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

# Set the path for Tesseract and Poppler on BIGFORCE
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
poppler_path = '/usr/bin/pdftotext'
os.environ['PATH'] += os.pathsep + poppler_path

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python your_script.py <pdf_folder_path> <output_folder> <input_pdf_list> [num_processes]")
        sys.exit(1)

    pdf_folder_path = sys.argv[1]
    output_folder = sys.argv[2]
    input_pdf_list = sys.argv[3]
    num_processes = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    process_pdf_folder(pdf_folder_path, output_folder, input_pdf_list, num_processes)
