#!/usr/bin/env python3
import os
import json
import re
import glob

# 定义输入和输出目录
ipt_dir = "/data/home/jdang/SIPO_PDF_B/results_frontpage/ocr_results_final"
opt_dir = "/data/home/jdang/SIPO_PDF_B/results_frontpage/"
optfile = "finish_ocr.txt"

# 确保输出目录存在
os.makedirs(opt_dir, exist_ok=True)

# 正则模式匹配 pnr
pnr_pattern = re.compile(r'CN\d+[A-Z]')

# 使用集合来存储唯一的 pnr
pnr_set = set()

# 判断是否是NDJSON格式
def is_ndjson(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                return line.startswith('{')
    return False

# 遍历所有 JSON 文件
for file_path in glob.glob(os.path.join(ipt_dir, '**', '*.json'), recursive=True):
    print(f"Processing file: {file_path}")
    
    # 判断文件格式（NDJSON 或标准 JSON）
    if is_ndjson(file_path):
        # 处理 NDJSON 格式（每行一个 JSON 对象）
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # 如果是列表，则遍历列表中的每一项
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        pnr = item.get("pnr", "")
                        match = pnr_pattern.search(pnr)
                        if match:
                            pnr_set.add(match.group())
                except json.JSONDecodeError:
                    continue
    else:
        # 处理标准 JSON 格式（整个文件是一个 JSON 对象）
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # 如果是列表，则遍历列表中的每一项
                items = data if isinstance(data, list) else [data]
                for item in items:
                    pnr = item.get("pnr", "")
                    match = pnr_pattern.search(pnr)
                    if match:
                        pnr_set.add(match.group())
            except json.JSONDecodeError:
                continue

# 将唯一的 pnr 写入输出文件
with open(os.path.join(opt_dir, optfile), 'w', encoding='utf-8') as outfile:
    for pnr in sorted(pnr_set):
        outfile.write(pnr + "\n")

print(f"所有唯一的 pnr 已提取到 {os.path.join(opt_dir, optfile)}")

