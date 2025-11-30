#!/usr/bin/env python3
"""
使用 arXiv API 抓取 cs.CV (计算机视觉) 类别的论文
并为每篇论文生成 Google Scholar 链接
"""
import requests
import xml.etree.ElementTree as ET
import time
import json
from pathlib import Path
from datetime import datetime


def fetch_cv_papers(max_results=100, start=0, sort_by='submittedDate', sort_order='descending', 
                    start_date=None, end_date=None):
    """
    从 arXiv 抓取 cs.CV 类别的论文
    
    Args:
        max_results: 每次请求最多返回的论文数量（arXiv API 限制最多2000）
        start: 起始位置（用于分页）
        sort_by: 排序方式 ('relevance', 'lastUpdatedDate', 'submittedDate')
        sort_order: 排序顺序 ('ascending', 'descending')
        start_date: 开始日期，格式 'YYYYMMDD' 或 'YYYYMMDDHHMMSS'，例如 '20250501'
        end_date: 结束日期，格式 'YYYYMMDD' 或 'YYYYMMDDHHMMSS'，例如 '20250531'
    
    Returns:
        论文列表，每个论文包含标题、作者、arXiv ID、摘要、发布日期、Google Scholar 链接等
    """
    base_url = "http://export.arxiv.org/api/query"
    
    # 构建查询字符串
    query = "cat:cs.CV"
    
    # 如果指定了日期范围，添加到查询中
    if start_date and end_date:
        # arXiv API 日期格式：YYYYMMDDHHMMSS
        # 如果只提供了日期，补充时间部分
        if len(start_date) == 8:
            start_date_full = f"{start_date}000000"
        else:
            start_date_full = start_date
        
        if len(end_date) == 8:
            end_date_full = f"{end_date}235959"
        else:
            end_date_full = end_date
        
        query = f"{query} AND submittedDate:[{start_date_full} TO {end_date_full}]"
    
    params = {
        'search_query': query,
        'start': start,
        'max_results': max_results,
        'sortBy': sort_by,
        'sortOrder': sort_order
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    print(f"正在抓取 arXiv cs.CV 论文...")
    print(f"参数: max_results={max_results}, start={start}, sort_by={sort_by}")
    if start_date and end_date:
        print(f"日期范围: {start_date} 到 {end_date}")
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        
        if response.status_code == 200:
            # 解析 XML 响应
            root = ET.fromstring(response.content)
            
            # arXiv API 使用 Atom 命名空间
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            
            entries = root.findall('atom:entry', ns)
            
            if not entries:
                print("未找到任何论文")
                return []
            
            papers = []
            for entry in entries:
                # 提取 arXiv ID
                arxiv_id = None
                id_text = entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else None
                if id_text:
                    # arXiv ID 格式: http://arxiv.org/abs/1234.5678v1
                    arxiv_id = id_text.split('/')[-1].split('v')[0]
                
                # 提取标题
                title_elem = entry.find('atom:title', ns)
                title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else None
                
                # 提取作者
                authors = []
                for author_elem in entry.findall('atom:author', ns):
                    name_elem = author_elem.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                
                # 提取摘要
                summary_elem = entry.find('atom:summary', ns)
                abstract = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else None
                
                # 提取发布日期
                published_elem = entry.find('atom:published', ns)
                published = published_elem.text.strip() if published_elem is not None else None
                year = None
                if published:
                    try:
                        year = int(published.split('-')[0])
                    except:
                        pass
                
                # 提取分类
                categories = []
                for category_elem in entry.findall('atom:category', ns):
                    term = category_elem.get('term')
                    if term:
                        categories.append(term)
                
                # 从 API 响应中提取链接
                # arXiv API 返回的链接类型：
                # - rel='alternate': arXiv 页面链接
                # - rel='related' title='pdf': PDF 链接
                arxiv_url = None
                pdf_url = None
                for link_elem in entry.findall('atom:link', ns):
                    rel = link_elem.get('rel')
                    title_attr = link_elem.get('title')
                    href = link_elem.get('href')
                    
                    if rel == 'alternate':
                        arxiv_url = href
                    elif rel == 'related' and title_attr == 'pdf':
                        pdf_url = href
                
                # 如果没有从 API 获取到链接，则手动构建（备用方案）
                if not arxiv_url and arxiv_id:
                    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
                if not pdf_url and arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                # 注意：Google Scholar 链接不是 arXiv API 返回的
                # arXiv API 只返回 arXiv 页面和 PDF 链接
                # 但是 arXiv 网页上有 Google Scholar 链接，格式为：
                # https://scholar.google.com/scholar_lookup?arxiv_id={arxiv_id}
                # 这比通过标题搜索更精确
                google_scholar_url = None
                if arxiv_id:
                    google_scholar_url = f"https://scholar.google.com/scholar_lookup?arxiv_id={arxiv_id}"
                
                paper = {
                    'arxiv_id': arxiv_id,
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'published': published,
                    'categories': categories,
                    'abstract': abstract[:500] if abstract else None,  # 限制摘要长度
                    'arxiv_url': arxiv_url,
                    'pdf_url': pdf_url,
                    'google_scholar_url': google_scholar_url
                }
                papers.append(paper)
            
            print(f"成功抓取 {len(papers)} 篇论文")
            return papers
            
        elif response.status_code == 429:
            print(f"⚠️  请求频率过高，等待 60 秒后重试...")
            time.sleep(60)
            return fetch_cv_papers(max_results, start, sort_by, sort_order, start_date, end_date)
        else:
            print(f"⚠️  HTTP 错误: {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
            return []
            
    except ET.ParseError as e:
        print(f"⚠️  XML 解析错误: {e}")
        return []
    except Exception as e:
        print(f"⚠️  错误: {e}")
        import traceback
        traceback.print_exc()
        return []


def fetch_all_cv_papers_by_date(start_date, end_date, batch_size=2000):
    """
    分页抓取指定日期范围内的所有 cs.CV 论文
    
    Args:
        start_date: 开始日期，格式 'YYYYMMDD'，例如 '20250501'
        end_date: 结束日期，格式 'YYYYMMDD'，例如 '20250531'
        batch_size: 每批抓取的数量（arXiv API 限制最多2000）
    
    Returns:
        所有论文的列表
    """
    all_papers = []
    start = 0
    
    print(f"\n开始抓取 {start_date} 到 {end_date} 的所有 cs.CV 论文...")
    print("=" * 80)
    
    while True:
        print(f"\n正在抓取第 {start // batch_size + 1} 批 (start={start})...")
        
        papers = fetch_cv_papers(
            max_results=batch_size,
            start=start,
            sort_by='submittedDate',
            sort_order='ascending',
            start_date=start_date,
            end_date=end_date
        )
        
        if not papers:
            print("没有更多论文了")
            break
        
        all_papers.extend(papers)
        print(f"本批抓取 {len(papers)} 篇，累计 {len(all_papers)} 篇")
        
        # 如果返回的论文数少于 batch_size，说明已经抓取完了
        if len(papers) < batch_size:
            print("已抓取所有论文")
            break
        
        start += batch_size
        
        # 避免请求过快，arXiv API 建议每次请求间隔 3 秒
        time.sleep(3.1)
    
    print(f"\n总共抓取 {len(all_papers)} 篇论文")
    return all_papers


def save_papers_to_json(papers, output_file):
    """将论文数据保存为 JSON 文件"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    
    print(f"\n论文数据已保存到: {output_path}")
    print(f"共 {len(papers)} 篇论文")


def print_papers_summary(papers, num_to_show=10):
    """打印论文摘要信息"""
    print("\n" + "=" * 80)
    print(f"论文摘要 (显示前 {min(num_to_show, len(papers))} 篇)")
    print("=" * 80)
    
    for idx, paper in enumerate(papers[:num_to_show], 1):
        print(f"\n[{idx}] {paper['title']}")
        print(f"    arXiv ID: {paper['arxiv_id']}")
        print(f"    作者: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
        print(f"    发布日期: {paper['published']}")
        print(f"    分类: {', '.join(paper['categories'])}")
        print(f"    arXiv URL: {paper['arxiv_url']}")
        print(f"    Google Scholar: {paper['google_scholar_url']}")
        if paper['abstract']:
            print(f"    摘要: {paper['abstract'][:150]}...")


if __name__ == "__main__":
    # 配置参数：抓取2025年1月到5月的所有论文
    START_DATE = "20250101"  # 2025年1月1日
    END_DATE = "20250531"    # 2025年5月31日
    BATCH_SIZE = 2000        # 每批最多抓取2000篇（arXiv API限制）
    
    # 注意：arXiv API 对单次查询的偏移量有限制（通常最多10000）
    # 如果论文数量超过10000，需要缩小日期范围分批查询
    # 使用分页功能抓取所有论文
    papers = fetch_all_cv_papers_by_date(
        start_date=START_DATE,
        end_date=END_DATE,
        batch_size=BATCH_SIZE
    )
    
    if papers:
        # 打印摘要
        print_papers_summary(papers, num_to_show=10)
        
        # 保存到 JSON 文件
        output_file = f"cv_papers_{START_DATE}_to_{END_DATE}.json"
        save_papers_to_json(papers, output_file)
        
        # 打印统计信息
        print("\n" + "=" * 80)
        print("统计信息")
        print("=" * 80)
        print(f"总论文数: {len(papers)}")
        print(f"有 Google Scholar 链接: {sum(1 for p in papers if p['google_scholar_url'])}")
        print(f"有摘要: {sum(1 for p in papers if p['abstract'])}")
        
        # 按年份统计
        years = {}
        for paper in papers:
            year = paper.get('year')
            if year:
                years[year] = years.get(year, 0) + 1
        
        if years:
            print("\n按年份分布:")
            for year in sorted(years.keys(), reverse=True):
                print(f"  {year}: {years[year]} 篇")
    else:
        print("未抓取到任何论文")

