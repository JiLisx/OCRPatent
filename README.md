# 运行main_ocr_bigforce_parse.py
- 需要在文件内指定pdf_folder_path和output_folder
- 已完成的finish文件仅限本次任务


# 运行main_ocr_bigforce_parse.py
- 列出finish文件 `find ./ -type f -name "*finish*.txt"`
- 全局生成finish和fail文件
  - `find ./ -name "finish*.txt" -exec sh -c 'if [ -s "{}" ]; then cat "{}"; fi' \; | sort | uniq > ./global_finish.txt`
  - `find ./ -name "failed*.txt" -exec sh -c 'if [ -s "{}" ]; then cat "{}"; fi' \; | sort | uniq > ./global_failed.txt`
- 给参数，运行main_ocr_bigforce_parse，处理某个子文件夹的pdf，并且跳过全局的finish文件，避免重复处理
  - `python3 main_ocr_bigforce_parse.py --pdf_folder_path ./CN117/ --output_folder ./ocr_results/CN117 --global_finish_file ./global_finish_continue.txt --global_failed_file ./global_failed_continue.txt --num_processes 10`


# 检查ocr情况

- 结合[dload_googlepatent](https://github.com/JiLisx/dload_googlepatent)的数据进行统计

## 截至2024年6月
- 所有已授权的专利数量：6949729（csv文件）
- 已下载的pdf专利数量：所有下载专利6943152，包括不在csv列表中的专利18410。（csv文件中已下载的专利数量为6931319）
- 已ocr的专利数量：（包括已下载但不在列表中的那些）
  - finish显示的已完成数量：6938900 `wc -l global_finish.txt`
  - json文件统计id已完成数量： 9178360 `find ./ -type f -name "*.json" -print0 | xargs -0 wc -l | awk '{sum += $1} END {print sum}'
  - json文件统计pnr的数量：6939180 `find ./ -type f -name "*.json" -print0 | xargs -0 grep -o '"pnr": "[^"]*"' | awk -F'"' '{print $4}' > ocr_count.txt`
  - json文件统计pnr并去重的数量：6938900 `sort ocr_count.txt | uniq > ocr_count_unique.txt

# OCRFullText


## 使用示例   

* 处理整个目录中的所有 PDF 文件，使用默认设置
  * @MAC
    ```python3 OCRFulltext.py ./pdftest/ --output ./results/ --workers 1```
  * @Bigforce
    ```python3 OCRFulltext.py ./CN117/ --output ./results/CN117/ --workers 5```

* 仅处理 pdflist.txt 中指定的 PDF 文件
  ```python3 OCRFulltext.py ./pdftest/ --output ./results --workers 1 --pdflist ./pdf_list.txt```


## Help

```
usage: Mac_OCRFulltext_parse.py [-h] [--output OUTPUT] [--workers WORKERS]
                                [--pdflist PDFLIST] [--lang LANG]
                                directory


批量处理目录下的所有 PDF 文件。

positional arguments:  
  directory             包含 PDF 文件的根目录路径  

optional arguments:
  -h, --help            show this help message and exit  
  --output OUTPUT       输出文件夹路径 (default: ./results/)  
  --workers WORKERS     并行处理的进程数 (default: 10)  
  --pdflist PDFLIST     可选的 PDF 列表文件路径（pdflist.txt）  
```


