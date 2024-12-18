#!/usr/local/bin/python3
import os
import json
import re
from datetime import datetime
import glob

ipt_dir1 = "/data/home/jdang/SIPO_PDF_B/ocr_results/reocr/patch2"
ipt_dir2 = "/data/home/jdang/SIPO_PDF_B/ocr_results/reocr/patch"
ipt_dir3 = "/data/home/jdang/SIPO_PDF_B/ocr_results"

opt_dir = "/data/home/jdang/SIPO_PDF_B/ocr_results/examiners"
opt_file = "examiners.txt"

if not os.path.exists(opt_dir):
    os.mkdir(opt_dir)
def load_pnr(pnrfile):
    gdate = {}
    with open(pnrfile,"r") as f:
        for line in f.readlines():
            gdate.update({line.split(",")[0]:line.split(",")[1].replace("\n","")})
    return gdate

def extract_examiner(pnr,left,right):
    if re.search("[申宙审]查员", left, re.IGNORECASE) is not None:
        examiner = re.findall("[申宙审]查员.*" + "\n", left, re.IGNORECASE)[0]
    else:
        examiner = re.findall("[申宙审]查员.*" + "\n", right, re.IGNORECASE)[0]
    examiner = examiner.strip()
    if examiner.__len__() > 0:
        with open(opt_dir + "/" + opt_file, "a") as g:
            g.write(pnr + "|" + examiner + "\n")

def search_in_file(file_name):
    with open(file_name, "r") as f:
        for line in f.readlines():
            descs = json.loads(line)
            if descs.__class__ == list:
                for desc in descs:
                    pnr = re.findall("CN[0-9]+[A-Z]", desc["pnr"])[0]
                    left = desc["left"].replace(" ", "")
                    right = desc["right"].replace(" ", "")
                    extract_examiner(pnr, left, right)
            else:
                desc = descs
                pnr = re.findall("CN[0-9]+[A-Z]", desc["pnr"])[0]
                left = desc["left"].replace(" ", "")
                right = desc["right"].replace(" ", "")
                extract_examiner(pnr, left, right)

def loop_files():
    for ipt_dir in [ipt_dir1,ipt_dir2,ipt_dir3]:
        for file_name in glob.glob(os.path.join(ipt_dir, '*', '*.json')):
            print(file_name)
            search_in_file(file_name)

if __name__ == '__main__':
    loop_files()