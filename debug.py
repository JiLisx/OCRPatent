#!/usr/local/bin/python3
import os
import json
import re
from datetime import datetime
import glob


def extract_ref(pnr,left,right,keyword):
    if re.search(keyword, left, re.IGNORECASE) is None:
        if re.search(keyword, right, re.IGNORECASE) is not None:
            refs = re.findall(keyword+"[\s\S]*", right, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(r"[a-z0-9]", line, re.IGNORECASE) is None:
                        break
                    print(pnr+"|"+line)
    else:
        if re.search("审查", left, re.IGNORECASE) is not None:
            refs = re.findall(keyword + "[\s\S]*", left, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(r"[a-z0-9]", line, re.IGNORECASE) is None:
                        break
                    print(pnr+"|"+line)
        else:
            refs = re.findall(keyword + "[\s\S]*", left, re.IGNORECASE)[0]
            for line in refs.split("\n")[1:]:
                if len(line) > 0:
                    if re.search(r"[a-z0-9]", line, re.IGNORECASE) is not None:
                        # continue
                        print(pnr+"|"+line)
            for line in right.split("\n"):
                if len(line) > 0:
                    if re.search(r"[a-z0-9]", line, re.IGNORECASE) is None:
                        break
                    print(pnr+"|"+line)

file_name = 'frontpage_reocr_patch2.json'

with open(file_name, "r") as f:
    for line in f.readlines():
        descs = json.loads(line)
        if descs.__class__ == list:
            for desc in descs:
                pnr = re.findall("CN[0-9]+[A-Z]", desc["pnr"])[0]
                left = desc["left"].replace(" ", "")
                right = desc["right"].replace(" ", "")
                if pnr == "CN100574349C":
                    break
                    extract_ref(pnr, left, right, keyword="参考文献")
                    extract_ref(pnr, left, right, keyword="对比文件")
        else:
            desc = descs
            pnr = re.findall("CN[0-9]+[A-Z]", desc["pnr"])[0]
            left = desc["left"].replace(" ", "")
            right = desc["right"].replace(" ", "")
            if pnr == "CN100574349C":
                break
            extract_ref(pnr, left, right, keyword="参考文献")
            extract_ref(pnr, left, right, keyword="对比文件")

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

def extract_examiner(pnr,left,right):
    if re.search("查员", left, re.IGNORECASE) is not None:
        examiner = re.findall("查员.*" + "\n", left, re.IGNORECASE)[0]
    else:
        examiner = re.findall("查员.*" + "\n", right, re.IGNORECASE)[0]
    print(examiner)