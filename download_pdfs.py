#!/usr/bin/env python3
import json
import subprocess
import os
import time
import random
from pathlib import Path
from datetime import datetime

# 配置
PDF_DIR = Path("/mnt/localssd/pdfs")
LOG_FILE = Path("./download_log.txt")
LOG_BUFFER_SIZE = 10  # 每10次存一次日志

# 创建保存PDF的目录
PDF_DIR.mkdir(parents=True, exist_ok=True)

# 日志缓冲区
log_buffer = []

def log_message(msg):
    """记录日志消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    log_buffer.append(log_entry + "\n")

def flush_log():
    """将日志缓冲区写入文件"""
    if log_buffer:
        with open(LOG_FILE, "a") as f:
            f.writelines(log_buffer)
        log_buffer.clear()

# 读取JSON文件
log_message("Loading JSON data...")
with open("gs_data_collection.json", "r") as f:
    data = json.load(f)

total = len(data)
log_message(f"Total papers: {total}")
log_message(f"Saving PDFs to: {PDF_DIR.absolute()}")
log_message(f"Saving logs to: {LOG_FILE.absolute()}")

# 统计
stats = {
    "success": 0,
    "skipped": 0,
    "failed": 0,
    "timeout": 0,
    "error": 0
}

# 下载每个PDF
start_time = time.time()
for i, paper in enumerate(data, 1):
    arxiv_id = paper["arxiv_id"]
    pdf_url = paper["pdf_url"]
    output_file = PDF_DIR / f"{arxiv_id}.pdf"
    
    # 如果文件已存在，跳过
    if output_file.exists():
        log_message(f"[{i}/{total}] Skipping {arxiv_id} (already exists)")
        stats["skipped"] += 1
    else:
        log_message(f"[{i}/{total}] Downloading {arxiv_id}...")
        
        # 使用wget下载
        try:
            subprocess.run(
                ["wget", "-q", "-O", str(output_file), pdf_url],
                check=True,
                timeout=60
            )
            log_message(f"  ✓ Downloaded {arxiv_id}.pdf")
            stats["success"] += 1
        except subprocess.TimeoutExpired:
            log_message(f"  ✗ Timeout for {arxiv_id}")
            if output_file.exists():
                output_file.unlink()
            stats["timeout"] += 1
        except subprocess.CalledProcessError as e:
            log_message(f"  ✗ Failed to download {arxiv_id}: {e}")
            if output_file.exists():
                output_file.unlink()
            stats["failed"] += 1
        except Exception as e:
            log_message(f"  ✗ Error for {arxiv_id}: {e}")
            if output_file.exists():
                output_file.unlink()
            stats["error"] += 1
    
    # 每10次保存日志
    if i % LOG_BUFFER_SIZE == 0:
        flush_log()
        log_message(f"Progress: {i}/{total} processed")
    
    # # 延迟避免被封（arXiv建议每3秒1个请求）
    # time.sleep(3 + random.uniform(0, 1))

# 保存剩余日志
flush_log()

# 最终统计
elapsed = time.time() - start_time
log_message("\n" + "="*50)
log_message("Download complete!")
log_message(f"Total time: {elapsed:.2f} seconds ({elapsed/3600:.2f} hours)")
log_message(f"Success: {stats['success']}")
log_message(f"Skipped: {stats['skipped']}")
log_message(f"Failed: {stats['failed']}")
log_message(f"Timeout: {stats['timeout']}")
log_message(f"Error: {stats['error']}")
log_message(f"PDFs saved in: {PDF_DIR.absolute()}")
log_message(f"Log saved in: {LOG_FILE.absolute()}")
flush_log()

