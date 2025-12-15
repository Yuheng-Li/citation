#!/usr/bin/env python3
"""
从1-5月的论文中随机采样n篇，获取Google Scholar数据（只提取ID）
"""
import json
import random
import time
import re
import requests
import os
from urllib.parse import quote_plus
from archived_code.old_approach.parse_name_and_id_from_gs_for_arxiv.gs_utils import extract_authors_from_gs_html

# Bright Data configuration
headers = {
    "Authorization": "Bearer 95f1e5b4c7ef79702fb77666561a234104bba6d008706c56d95f27dcae3daa9a",
    "Content-Type": "application/json"
}

def build_google_scholar_search_url(title, authors):
    """构建 Google Scholar 搜索 URL"""
    query_parts = [title]
    top_authors = authors[:5] if len(authors) > 5 else authors
    query_parts.extend(top_authors)
    search_query = " ".join(query_parts)
    encoded_query = quote_plus(search_query)
    url = f"https://scholar.google.com/scholar?q={encoded_query}"
    return url

def fetch_google_scholar_page(url, timeout=30):
    """使用 Bright Data API 获取 Google Scholar 页面"""
    data = {
        "zone": "yuheng_serp",
        "url": url,
        "format": "raw"
    }
    
    try:
        response = requests.post(
            "https://api.brightdata.com/request",
            json=data,
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code == 200:
            if "not supported" in response.text.lower():
                return None
            if len(response.text) < 100:
                return None
            return response.text
        else:
            return None
    except Exception as e:
        print(f"  ⚠️  错误: {e}")
        return None

def extract_scholar_ids_from_html(html):
    """从 HTML 中提取所有 Google Scholar IDs"""
    pattern = r'/citations\?user=([^&"\']+)'
    scholar_ids = list(set(re.findall(pattern, html)))
    return scholar_ids

def extract_citation_count_from_html(html):
    """从 HTML 中提取引用数量"""
    # 简单的正则表达式提取 "Cited by X"
    match = re.search(r'Cited by\s+(\d+)', html, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except:
            pass
    return None

def safe_save_json(data, output_file):
    """安全地保存 JSON 文件（原子写入）"""
    temp_file = output_file + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, output_file)  # 原子替换
        return True
    except Exception as e:
        print(f"  ⚠️  保存失败: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def main():
    # 配置参数
    sample_size = 4000  # 随机采样的论文数量
    output_file = "gs_data_collection.json"
    raw_html_dir = "/mnt/localssd/raw_html"  # raw HTML 保存目录
    
    # 创建 raw HTML 保存目录
    os.makedirs(raw_html_dir, exist_ok=True)
    print(f"raw HTML 保存目录: {raw_html_dir}\n")
    
    # 加载论文数据
    json_file = "cv_papers_20230101_to_20250531.json"
    print(f"加载论文数据: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        all_papers = json.load(f)
    
    print(f"总论文数: {len(all_papers)}")
    
    # 检查是否有已处理的结果文件
    processed_arxiv_ids = set()
    existing_results = []
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_results = json.load(f)
            processed_arxiv_ids = {paper.get('arxiv_id') for paper in existing_results if paper.get('arxiv_id')}
            print(f"发现已处理的结果文件: {output_file}")
            print(f"已处理的论文数: {len(processed_arxiv_ids)}")
    except FileNotFoundError:
        print(f"未找到已处理的结果文件，将从头开始")
    except Exception as e:
        print(f"⚠️  读取已处理结果文件时出错: {e}，将从头开始")
    
    # 从所有论文中移除已处理的论文
    remaining_papers = [paper for paper in all_papers if paper.get('arxiv_id') not in processed_arxiv_ids]
    
    print(f"剩余未处理的论文数: {len(remaining_papers)}")
    print(f"随机采样: {sample_size} 篇论文\n")
    
    if len(remaining_papers) == 0:
        print("⚠️  所有论文都已处理完成！")
        return
    
    if len(remaining_papers) < sample_size:
        print(f"⚠️  剩余论文数 ({len(remaining_papers)}) 少于采样数量 ({sample_size})，将处理所有剩余论文")
        sample_size = len(remaining_papers)
    
    # 随机采样 n 篇论文
    sampled_papers = random.sample(remaining_papers, sample_size)
    
    results = existing_results.copy()  # 保留已有结果
    
    # 保存间隔
    save_interval = 100
    initial_count = len(existing_results)  # 记录初始数量
    
    for idx, paper in enumerate(sampled_papers, 1):
        arxiv_id = paper.get('arxiv_id', '')
        arxiv_authors = paper.get('authors', [])
        title = paper.get('title', '')
        
        print(f"[{idx}/{len(sampled_papers)}] arXiv ID: {arxiv_id}")
        print(f"  标题: {title[:60]}...")
        
        # 构建搜索 URL
        gs_search_url = build_google_scholar_search_url(title, arxiv_authors)
        
        # 构建结果：保留原始论文的所有信息
        result = paper.copy()
        # 移除 authors 字段，使用 arxiv_authors 替代
        if 'authors' in result:
            result['arxiv_authors'] = result.pop('authors')
        else:
            result['arxiv_authors'] = arxiv_authors
        
        # 添加 Google Scholar 相关字段
        result['gs_search_url'] = gs_search_url
        
        # 获取 Google Scholar 页面
        try:
            html = fetch_google_scholar_page(gs_search_url)
            
            if html:
                # 保存 raw HTML 到文件
                html_filename = f"{arxiv_id.replace('/', '_')}.html"
                html_filepath = os.path.join(raw_html_dir, html_filename)
                try:
                    with open(html_filepath, 'w', encoding='utf-8') as html_file:
                        html_file.write(html)
                    print(f"  💾 已保存 HTML: {html_filename}")
                except Exception as e:
                    print(f"  ⚠️  保存 HTML 失败: {e}")
                
                # 提取 Google Scholar IDs
                scholar_ids = extract_scholar_ids_from_html(html)
                
                # 提取引用数量
                citation_count = extract_citation_count_from_html(html)
                
                # 提取作者数量（使用旧版本的函数）
                gs_author_count = None
                try:
                    authors_list, is_truncated, raw_text = extract_authors_from_gs_html(html, title=title)
                    if authors_list is not None:  # None 表示多个匹配结果
                        gs_author_count = len(authors_list)
                except Exception as e:
                    # 如果提取作者数量失败，不影响整体流程
                    print(f"  ⚠️  提取作者数量失败: {e}")
                
                result['gs_search_success'] = True
                result['gs_authors'] = scholar_ids  # 只保存 ID 列表
                result['citation_count'] = citation_count
                result['gs_author_count'] = gs_author_count
                result['raw_html_filename'] = html_filename  # 添加 HTML 文件名
                
                print(f"  ✅ 成功提取 {len(scholar_ids)} 个 ID，{gs_author_count} 个作者")
            else:
                print(f"  ❌ 无法获取 Google Scholar 页面")
                result['gs_search_success'] = False
                result['gs_authors'] = []
                result['citation_count'] = None
                result['gs_author_count'] = None
                result['raw_html_filename'] = None
                result['error_type'] = "fetch_failed"
        except Exception as e:
            # 检查是否是超时错误
            error_str = str(e).lower()
            if 'timeout' in error_str or 'timed out' in error_str:
                error_type = "timeout"
                print(f"  ❌ 请求超时")
            else:
                error_type = "fetch_failed"
                print(f"  ❌ 获取失败: {e}")
            
            result['gs_search_success'] = False
            result['gs_authors'] = []
            result['citation_count'] = None
            result['gs_author_count'] = None
            result['raw_html_filename'] = None
            result['error_type'] = error_type
        
        results.append(result)
        print()
        
        # 每处理10篇保存一次（使用原子写入）
        if idx % save_interval == 0:
            if safe_save_json(results, output_file):
                print(f"  💾 已保存 {len(results)} 篇论文（每 {save_interval} 篇自动保存）\n")
        
        # 避免请求过快
        time.sleep(0.05)
    
    # 最后保存一次（确保所有结果都保存了，使用原子写入）
    if not safe_save_json(results, output_file):
        raise Exception("最终保存失败")
    
    print(f"\n结果已保存到: {output_file}")
    print(f"总共处理: {len(results)} 篇论文（包含之前已处理的 {initial_count} 篇）")
    success_count = sum(1 for r in results if r.get('gs_search_success', False))
    print(f"成功获取: {success_count} 篇")
    print(f"本次新增: {len(results) - initial_count} 篇")

if __name__ == "__main__":
    main()

