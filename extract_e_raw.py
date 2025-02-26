#!/usr/local/bin/python3
import os
import json
import re
from datetime import datetime
import glob

ipt_dir = "/data/home/jdang/SIPO_PDF_B/results_frontpage"
opt_dir = "/data/home/jdang/SIPO_PDF_B/results_frontpage"
pnrfile = "/data/home/jdang/SIPO_PDF_B/gdate2406.csv"
pnr_pos = "pnr_pos.txt"
finished = "finished.txt"
opt_file = "refs.txt"
label = r"[0-9]{4,}[A-Z]|[A-Z].*[0-9]{4,}"

if not os.path.exists(opt_dir):
    os.mkdir(opt_dir)

if not os.path.exists(os.path.join(opt_dir, pnr_pos)):
    with open(os.path.join(opt_dir, pnr_pos), 'w') as file:
        pass

if not os.path.exists(os.path.join(opt_dir, finished)):
    with open(os.path.join(opt_dir, finished), 'w') as file:
        pass

def load_pnr(pnrfile):
    gdate = {}
    with open(pnrfile, "r") as f:
        for line in f.readlines():
            gdate.update({line.split(",")[0]: line.split(",")[1].replace("\n", "")})
    return gdate

def load_finished_pt(opt_dir, pnr_pos):
    finished_pts = []
    with open(os.path.join(opt_dir, pnr_pos), "r") as f:
        for line in f.readlines():
            finished_pts.append({line.split("|")[0].replace("\n", "")})
    return finished_pts

def load_finished_files(opt_dir, finished):
    finished_files = []
    with open(os.path.join(opt_dir, finished), "r") as f:
        for line in f.readlines():
            finished_files.append(line.replace("\n", ""))
    return finished_files

def extract_ref(pnr, left, right, keyword, opt_dir, opt_file):
    if re.search(keyword, left, re.IGNORECASE) is None:
        if re.search(keyword, right, re.IGNORECASE) is not None:
            refs = re.findall(keyword+"[\s\S]*", right, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(label, line, re.IGNORECASE) is not None:
                        with open(os.path.join(opt_dir, opt_file), "a") as g:
                            g.write(pnr + "|" + line + "\n")
    else:
        if re.search("审查", left, re.IGNORECASE) is not None:
            refs = re.findall(keyword+"[\s\S]*", left, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(label, line, re.IGNORECASE) is not None:
                        with open(os.path.join(opt_dir, opt_file), "a") as g:
                            g.write(pnr + "|" + line + "\n")
        else:
            refs = re.findall(keyword+"[\s\S]*", left, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(label, line, re.IGNORECASE) is not None:
                        with open(os.path.join(opt_dir, opt_file), "a") as g:
                            g.write(pnr + "|" + line + "\n")
            for line in right.split("\n"):
                if len(line) > 0:
                    if re.search(label, line, re.IGNORECASE) is not None:
                        with open(os.path.join(opt_dir, opt_file), "a") as g:
                            g.write(pnr + "|" + line + "\n")

def ExtractFile(file_name,gdate,opt_dir,pnr_pos,dt2: datetime,finished_pts,second = True):
    with open(file_name, "r") as f:
        for line in f.readlines():
            descs = json.loads(line)
            if descs.__class__ == list:
                for desc in descs:
                    pnr = re.findall("CN[0-9]+[A-Z]", desc["pnr"])[0]
                    if pnr not in finished_pts:
                        if second:
                            left1 = desc["left1"].replace(" ", "")
                            right1 = desc["right1"].replace(" ", "")
                            left2 = desc["left2"].replace(" ", "")
                            right2 = desc["right2"].replace(" ", "")
                            if pnr in gdate.keys():
                                dt1 = datetime.strptime(gdate[pnr], "%Y-%m-%d")
                                if dt1 < dt2:
                                    extract_ref(pnr, left1, right1, keyword="参考文献",opt_dir = opt_dir, opt_file = opt_file)
                                    extract_ref(pnr, left2, right2, keyword="参考文献",opt_dir = opt_dir, opt_file = opt_file)
                                else:
                                    extract_ref(pnr, left1, right1, keyword="对比文件",opt_dir = opt_dir, opt_file = opt_file)
                                    extract_ref(pnr, left2, right2, keyword="对比文件",opt_dir = opt_dir, opt_file = opt_file)
                        else:
                            left = desc["left"].replace(" ", "")
                            right = desc["right"].replace(" ", "")
                            if pnr in gdate.keys():
                                dt1 = datetime.strptime(gdate[pnr], "%Y-%m-%d")
                                if dt1 < dt2:
                                    extract_ref(pnr = pnr, left = left, right = right, keyword="参考文献",opt_dir = opt_dir, opt_file = opt_file)
                                else:
                                    extract_ref(pnr = pnr, left = left, right = right, keyword="对比文件",opt_dir = opt_dir, opt_file = opt_file)
                        with open(os.path.join(opt_dir, pnr_pos), "a") as g:
                            g.write(pnr + "|" + file_name + "\n")
            else:
                desc = descs
                pnr = re.findall("CN[0-9]+[A-Z]", desc["pnr"])[0]
                if pnr not in finished_pts:
                    if second:
                        left1 = desc["left1"].replace(" ", "")
                        right1 = desc["right1"].replace(" ", "")
                        left2 = desc["left2"].replace(" ", "")
                        right2 = desc["right2"].replace(" ", "")
                        if pnr in gdate.keys():
                            dt1 = datetime.strptime(gdate[pnr], "%Y-%m-%d")
                            if dt1 < dt2:
                                extract_ref(pnr, left1, right1, keyword="参考文献",opt_dir = opt_dir, opt_file = opt_file)
                                extract_ref(pnr, left2, right2, keyword="参考文献",opt_dir = opt_dir, opt_file = opt_file)
                            else:
                                extract_ref(pnr, left1, right1, keyword="对比文件",opt_dir = opt_dir, opt_file = opt_file)
                                extract_ref(pnr, left2, right2, keyword="对比文件",opt_dir = opt_dir, opt_file = opt_file)
                    else:
                        left = desc["left"].replace(" ", "")
                        right = desc["right"].replace(" ", "")
                        if pnr in gdate.keys():
                            dt1 = datetime.strptime(gdate[pnr], "%Y-%m-%d")
                            if dt1 < dt2:
                                extract_ref(pnr, left, right, keyword="参考文献",opt_dir = opt_dir, opt_file = opt_file)
                            else:
                                extract_ref(pnr, left, right, keyword="对比文件",opt_dir = opt_dir, opt_file = opt_file)
                    with open(os.path.join(opt_dir, pnr_pos), "a") as g:
                        g.write(pnr + "|" + file_name + "\n")

def loop_files():
    dt2 = datetime.strptime("2010-04-07", "%Y-%m-%d")
    for file_name in glob.glob(os.path.join(ipt_dir, '*', '*.json')):
        print(file_name)
        if file_name not in finished_files:
            if file_name == os.path.join(ipt_dir, 'second', 'second.json'):
                ExtractFile(file_name = file_name, gdate = gdate, opt_dir = opt_dir, pnr_pos = pnr_pos, second = True, dt2 = dt2, finished_pts = finished_pts)
            else:
                ExtractFile(file_name = file_name, gdate = gdate, opt_dir = opt_dir, pnr_pos = pnr_pos, second = False, dt2 = dt2, finished_pts = finished_pts)
            with open(os.path.join(opt_dir, finished), "a") as g:
                        g.write(file_name + "\n")


if __name__ == '__main__':
    gdate = load_pnr(pnrfile)
    print("load grant date file")
    finished_pts = load_finished_pt(opt_dir, pnr_pos)
    finished_files = load_finished_files(opt_dir, finished)
    print("load finished patents and files")
    loop_files()
