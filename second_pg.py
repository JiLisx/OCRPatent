#!/usr/local/bin/python3
import os
import json
import re
from datetime import datetime
import glob

ipt_dir = "/data/home/jdang/SIPO_PDF_B/ocr_results"
opt_dir = "/data/home/jdang/SIPO_PDF_B/ocr_results"
if not os.path.exists(opt_dir):
    os.mkdir(opt_dir)

def loop_files():
    for file_name in glob.glob(os.path.join(ipt_dir, '*','*.json')):
        print(file_name)
        with open(file_name,"r") as f:
            for line in f.readlines():
                descs = json.loads(line)
                if descs.__class__ == list :
                    for desc in descs:
                        pnr = re.findall("CN[0-9]+[A-Z]",desc["pnr"])[0]
                        left = desc["left"].replace(" ", "")
                        right = desc["right"].replace(" ", "")
                        if re.search("续页", left, re.IGNORECASE) is not None or re.search("续页", right, re.IGNORECASE) is not None:
                            with open(opt_dir + "/second_pg.txt", "a") as g:
                                g.write(pnr + "\n")
                else:
                    desc = descs
                    pnr = re.findall("CN[0-9]+[A-Z]",desc["pnr"])[0]
                    left = desc["left"].replace(" ", "")
                    right = desc["right"].replace(" ", "")
                    if re.search("续页", left, re.IGNORECASE) is not None or re.search("续页", right, re.IGNORECASE) is not None:
                        with open(opt_dir + "/second_pg.txt", "a") as g:
                            g.write(pnr + "\n")

if __name__ == '__main__':
    loop_files()