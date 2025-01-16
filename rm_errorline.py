#!/usr/bin/env python3
import os
import json
import re
import glob
import shutil

# ==Settings======================
ipt_dir = "/data/home/jdang/SIPO_PDF_B/results_frontpage/ocr_results_remove_reocrpatch"
opt_dir = "/data/home/jdang/SIPO_PDF_B/results_frontpage/ocr_results_final"
patch_list_dir = "/data/home/jdang/SIPO_PDF_B/patch_list/second"

def read_pnr_from_file(file_path):
    """
    从指定文件中读取 PNR 并返回一个集合。
    支持 TXT 和 CSV 格式的文件，假设每行包含一个 PNR。
    """
    pnr_set = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # 使用正则表达式提取 PNR（例如 CN12345A）
                matches = re.findall(r"CN\d+[A-Z]", line)
                if matches:
                    pnr_set.add(matches[0])
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    return pnr_set


def gather_pnr_lists():
    """
    收集所有需要排除的 PNR，包括错误处理 PNR 和“续页” PNR。
    返回一个包含所有需排除 PNR 的集合。
    """
    # 定义需要匹配的 PNR 文件模式
    pnr_patterns = [
        '*',  # 匹配所有文件
    ]

    exclude_pnr_set = set()

    # 收集所有 PNR 文件
    for pattern in pnr_patterns:
        matched_files = glob.glob(os.path.join(patch_list_dir, pattern))
        if matched_files:
            print(f"找到 {len(matched_files)} 个需要排除的列表文件：")
            for file in matched_files:
                pnr_set = read_pnr_from_file(file)
                exclude_pnr_set.update(pnr_set)
        else:
            print(f"未找到任何需要排除的列表文件。")
    return exclude_pnr_set


def process_json_file(file_path, output_path, exclude_pnr_set):
    """
    处理单个 JSON 文件：
    - 如果 JSON 数据是列表，删除包含需排除 PNR 的条目。
    - 如果 JSON 数据是单个字典，检查 PNR 是否需排除。
    - 如果 JSON 文件包含多行 JSON 对象（如 NDJSON），逐行处理。
    - 根据处理结果，决定是保存修改后的文件还是复制原文件。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # 尝试一次性加载整个文件
            try:
                data = json.load(f)
                single_load = True
            except json.JSONDecodeError:
                # 如果失败，尝试逐行加载（假设是多行 JSON 对象）
                f.seek(0)
                data = [json.loads(line) for line in f if line.strip()]
                single_load = False
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return

    modified = False

    if single_load:
        if isinstance(data, list):
            # 处理列表中的每个条目
            filtered_data = []
            for entry in data:
                pnr = entry.get("pnr", "")
                pnr_matches = re.findall(r"CN\d+[A-Z]", pnr)
                if pnr_matches:
                    pnr_extracted = pnr_matches[0]
                    if pnr_extracted not in exclude_pnr_set:
                        filtered_data.append(entry)
                    else:
                        modified = True
                        print(f"排除条目 PNR: {pnr_extracted} 在文件: {file_path}")
                else:
                    # 如果没有找到 PNR，保留条目
                    filtered_data.append(entry)

            if modified:
                if filtered_data:
                    # 保存修改后的 JSON 文件
                    with open(output_path, "w", encoding="utf-8") as f_out:
                        json.dump(filtered_data, f_out, ensure_ascii=False, indent=4)
                    print(f"已修改并保存文件: {output_path}")
                else:
                    # 如果所有条目都被删除，生成一个空数组
                    with open(output_path, "w", encoding="utf-8") as f_out:
                        json.dump([], f_out, ensure_ascii=False, indent=4)
                    print(f"所有条目被排除，生成空数组文件: {output_path}")
            else:
                # 复制原文件
                shutil.copy2(file_path, output_path)
                print(f"未发现需修改的条目，已复制原文件: {output_path}")

        elif isinstance(data, dict):
            # 处理单个字典条目
            pnr = data.get("pnr", "")
            pnr_matches = re.findall(r"CN\d+[A-Z]", pnr)
            if pnr_matches:
                pnr_extracted = pnr_matches[0]
                if pnr_extracted in exclude_pnr_set:
                    # 跳过该文件，不进行复制
                    print(f"文件 {file_path} 的 PNR ({pnr_extracted}) 需要被排除，已跳过。")
                    return
            # 复制原文件
            shutil.copy2(file_path, output_path)
            print(f"已复制单条目文件: {output_path}")

        else:
            # 未知 JSON 结构，直接复制文件
            shutil.copy2(file_path, output_path)
            print(f"已复制未知结构文件: {output_path}")

    else:
        # 处理多行 JSON 对象（如 NDJSON）
        filtered_data = []
        modified = False
        for entry in data:
            pnr = entry.get("pnr", "")
            pnr_matches = re.findall(r"CN\d+[A-Z]", pnr)
            if pnr_matches:
                pnr_extracted = pnr_matches[0]
                if pnr_extracted not in exclude_pnr_set:
                    filtered_data.append(entry)
                else:
                    modified = True
                    print(f"排除条目 PNR: {pnr_extracted} 在文件: {file_path}")
            else:
                # 如果没有找到 PNR，保留条目
                filtered_data.append(entry)

        if modified:
            if filtered_data:
                # 保存修改后的 JSON 文件为 NDJSON 格式
                with open(output_path, "w", encoding="utf-8") as f_out:
                    for entry in filtered_data:
                        json.dump(entry, f_out, ensure_ascii=False)
                        f_out.write('\n')
                print(f"已修改并保存文件（NDJSON 格式）: {output_path}")
            else:
                # 如果所有条目都被删除，生成一个空文件
                open(output_path, 'w').close()
                print(f"所有条目被排除，生成空文件: {output_path}")
        else:
            # 复制原文件
            shutil.copy2(file_path, output_path)
            print(f"未发现需修改的条目，已复制原文件: {output_path}")


def loop_files(exclude_pnr_set):
    """
    遍历所有 JSON 文件并处理。
    """
    # 查找所有 JSON 文件（递归）
    json_files = glob.glob(os.path.join(ipt_dir, '**', '*.json'), recursive=True)
    print(f"共找到 {len(json_files)} 个 JSON 文件需要处理。")

    for file_path in json_files:
        # 生成输出文件的路径，保持目录结构
        relative_path = os.path.relpath(file_path, ipt_dir)
        output_path = os.path.join(opt_dir, relative_path)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 处理 JSON 文件
        process_json_file(file_path, output_path, exclude_pnr_set)


# ================================
# 主程序部分
# ================================

if __name__ == "__main__":
    # 收集所有需排除的 PNR
    exclude_pnr_set = gather_pnr_lists()

    if exclude_pnr_set:
        # 处理所有 JSON 文件
        loop_files(exclude_pnr_set)
    else:
        print("没有 PNR 被排除，所有 JSON 文件将被复制到输出目录。")
        # 如果没有 PNR 需要排除，直接复制所有文件
        json_files = glob.glob(os.path.join(ipt_dir, '**', '*.json'), recursive=True)
        print(f"共找到 {len(json_files)} 个 JSON 文件需要复制。")
        for file_path in json_files:
            relative_path = os.path.relpath(file_path, ipt_dir)
            output_path = os.path.join(opt_dir, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy2(file_path, output_path)
            print(f"已复制文件: {output_path}")

    print("所有文件处理完成。")
