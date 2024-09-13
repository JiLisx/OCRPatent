import os
import json
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import multiprocessing
from tqdm import tqdm
from functools import partial
import argparse

# Set the path for Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Set the path for Poppler
poppler_path = '/usr/bin/pdftotext'
os.environ['PATH'] += os.pathsep + poppler_path

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
        return left_img, right_img
    except Exception as e:
        raise RuntimeError(f"Error during image splitting: {e}")


def ocr_image(img):
    try:
        # print('ocr_image begin...')
        text = pytesseract.image_to_string(img, lang='chi_sim')
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


def process_pdf_folder(folder_path, output_folder, num_processes=10):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    finish_file = os.path.join(output_folder, "finish_continue.txt")
    failed_file = os.path.join(output_folder, "failed_continue.txt")
    json_file = os.path.join(output_folder, "frontpage_result999_continue.json")

    if not os.path.exists(finish_file):
        open(finish_file, 'w').close()

    if not os.path.exists(failed_file):
        open(failed_file, 'w').close()

    with open(finish_file, 'r') as file:
        finished_pdfs = set(line.strip() for line in file.readlines())

    with open(failed_file, 'r') as file:
        failed_pdfs = set(line.strip() for line in file.readlines())

    pdf_files = []
    for root, _, files in os.walk(folder_path):
        if "dload" in root:
            continue
        for file in files:
            if file.endswith('.pdf'):
                pnr = os.path.basename(file).split('.')[0]
                if pnr not in finished_pdfs and pnr not in failed_pdfs:
                    pdf_files.append(os.path.relpath(os.path.join(root, file), folder_path))

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf_folder_path', type=str, default='./', help='Path to the PDF folder')
    parser.add_argument('--output_folder', type=str, default='./ocr_results/', help='Path to the output folder')
    parser.add_argument('--num_processes', type=int, default=5, help='Number of processes to use')
    args = parser.parse_args()

    process_pdf_folder(args.pdf_folder_path, args.output_folder, num_processes=args.num_processes)

