#!/usr/local/bin/python3
import os
import json
import re
from datetime import datetime
import glob

ipt_dir = "/data/home/jdang/SIPO_PDF_B/ocr_results/reocr/patch3"
opt_dir = "/data/home/jdang/SIPO_PDF_B/ocr_results/refs"
pnrfile = "/data/home/jdang/SIPO_PDF_B/ocr_results/gdate.csv"
opt_file = "refs_patch3.txt"
label = r"[0-9]{4,}[A-Z]|[A-Z].*[0-9]{4,}"

if not os.path.exists(opt_dir):
    os.mkdir(opt_dir)
def load_pnr(pnrfile):
    gdate = {}
    with open(pnrfile,"r") as f:
        for line in f.readlines():
            gdate.update({line.split(",")[0]:line.split(",")[1].replace("\n","")})
    return gdate

def extract_ref(pnr,left,right,keyword):
    if re.search(keyword, left, re.IGNORECASE) is None:
        if re.search(keyword, right, re.IGNORECASE) is not None:
            refs = re.findall(keyword+"[\s\S]*", right, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(label, line, re.IGNORECASE) is not None:
                        # break
                        with open(opt_dir + "/" + opt_file, "a") as g:
                            g.write(pnr + "|" + line + "\n")
    else:
        if re.search("审查", left, re.IGNORECASE) is not None:
            refs = re.findall(keyword + "[\s\S]*", left, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(label, line, re.IGNORECASE) is not None:
                        # break
                        with open(opt_dir + "/" + opt_file, "a") as g:
                            g.write(pnr + "|" + line + "\n")
        else:
            refs = re.findall(keyword + "[\s\S]*", left, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(label, line, re.IGNORECASE) is not None:
                        # continue
                        with open(opt_dir +  "/" + opt_file, "a") as g:
                            g.write(pnr + "|" + line + "\n")
            for line in right.split("\n"):
                if len(line) > 0:
                    if re.search(label, line, re.IGNORECASE) is not None:
                        # break
                        with open(opt_dir +  "/" + opt_file, "a") as g:
                            g.write(pnr + "|" + line + "\n")
def loop_files():
    dt2 = datetime.strptime("2010-04-07", "%Y-%m-%d")
    for file_name in glob.glob(os.path.join(ipt_dir, '*','*.json')):
        print(file_name)
        with open(file_name,"r") as f:
            for line in f.readlines():
                descs = json.loads(line)
                if descs.__class__ == list :
                    for desc in descs:
                        # if desc != "\n":
                        pnr = re.findall("CN[0-9]+[A-Z]",desc["pnr"])[0]
                        left = desc["left"].replace(" ", "")
                        right = desc["right"].replace(" ", "")
                        # record the file name of each patent
                        with open(opt_dir+"/pnr_pos.txt","a") as g:
                            g.write(pnr+"|"+file_name+"\n")
                        if pnr in gdate.keys():
                            dt1 = datetime.strptime(gdate[pnr], "%Y-%m-%d")
                            if dt1 < dt2:
                                extract_ref(pnr,left,right,keyword="参考文献")
                            else:
                                extract_ref(pnr,left, right, keyword="对比文件")
                else:
                    desc = descs
                    pnr = re.findall("CN[0-9]+[A-Z]",desc["pnr"])[0]
                    left = desc["left"].replace(" ", "")
                    right = desc["right"].replace(" ", "")
                    # record the file name of each patent
                    with open(opt_dir + "/pnr_pos.txt", "a") as g:
                        g.write(pnr + "|" + file_name + "\n")
                    if pnr in gdate.keys():
                        dt1 = datetime.strptime(gdate[pnr], "%Y-%m-%d")
                        if dt1 < dt2:
                            extract_ref(pnr, left, right, keyword="参考文献")
                        else:
                            extract_ref(pnr, left, right, keyword="对比文件")

if __name__ == '__main__':
    gdate = load_pnr(pnrfile)
    print("loaded grant date file")
    loop_files()