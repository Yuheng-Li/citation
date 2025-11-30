#!/usr/bin/env python3
"""
测试 arXiv 覆盖率：随机采样 100 篇论文，看能在 arXiv 上找到多少
"""
import json
import random
import time
from pathlib import Path
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import sys

# 添加父目录到路径，以便导入profile_reader
sys.path.append(str(Path(__file__).parent.parent))
from crawling_profiles.profile_reader import collect_all_papers


def search_arxiv(title, author=None):
    """
    使用 arXiv API 搜索论文
    API 文档: https://arxiv.org/help/api/user-manual
    """
    base_url = "http://export.arxiv.org/api/query"
    
    # 构建查询字符串
    # arXiv 查询语法: ti:title, au:author, all:all fields
    if author:
        # 尝试用标题和作者搜索
        query = f'ti:"{title}" AND au:"{author}"'
    else:
        query = f'ti:"{title}"'
    
    params = {
        'search_query': query,
        'start': 0,
        'max_results': 3,  # 最多返回3个结果
        'sortBy': 'relevance',
        'sortOrder': 'descending'
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 解析 XML 响应
            root = ET.fromstring(response.content)
            
            # arXiv API 使用 Atom 命名空间
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            
            entries = root.findall('atom:entry', ns)
            
            if not entries:
                return None
            
            results = []
            for entry in entries:
                # 提取 arXiv ID
                arxiv_id = None
                id_text = entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else None
                if id_text:
                    # arXiv ID 格式: http://arxiv.org/abs/1234.5678v1
                    arxiv_id = id_text.split('/')[-1].split('v')[0]
                
                # 提取标题
                title_elem = entry.find('atom:title', ns)
                arxiv_title = title_elem.text.strip() if title_elem is not None else None
                
                # 提取作者
                authors = []
                for author_elem in entry.findall('atom:author', ns):
                    name_elem = author_elem.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                
                # 提取摘要
                summary_elem = entry.find('atom:summary', ns)
                abstract = summary_elem.text.strip() if summary_elem is not None else None
                
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
                
                # 构建 PDF URL（arXiv 所有论文都有 PDF）
                pdf_url = None
                if arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                # 构建 arXiv 页面 URL
                arxiv_url = None
                if arxiv_id:
                    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
                
                result = {
                    'arxiv_id': arxiv_id,
                    'title': arxiv_title,
                    'authors': authors,
                    'year': year,
                    'published': published,
                    'categories': categories,
                    'abstract': abstract,
                    'url': arxiv_url,
                    'pdf_url': pdf_url  # arXiv 所有论文都有 PDF
                }
                results.append(result)
            
            return results
            
        elif response.status_code == 429:
            print(f"  ⚠️  Rate limit exceeded, waiting...")
            time.sleep(60)  # 等待1分钟
            return search_arxiv(title, author)  # 重试
        else:
            print(f"  ⚠️  HTTP {response.status_code}")
            return None
            
    except ET.ParseError as e:
        print(f"  ⚠️  XML Parse Error: {e}")
        return None
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return None


# collect_all_papers 函数已移至 profile_reader.py，现在直接导入使用


def test_arxiv_coverage(all_papers, sample_size=100):
    """测试 arXiv 覆盖率"""
    # 随机打乱并采样
    random.shuffle(all_papers)
    sampled_papers = all_papers[:sample_size]
    
    print(f"\n随机采样 {len(sampled_papers)} 篇论文进行测试\n")
    print("=" * 80)
    
    found_count = 0
    not_found_count = 0
    pdf_available_count = 0  # 有 PDF URL 的数量（arXiv 所有论文都有 PDF）
    
    results = []
    
    for idx, paper in enumerate(sampled_papers, 1):
        title = paper['title']
        author = paper['author_name']
        
        print(f"[{idx}/{len(sampled_papers)}] 搜索: {title[:60]}...")
        print(f"  作者: {author}")
        
        arxiv_results = search_arxiv(title, author=author)
        
        result = {
            'paper': paper,
            'arxiv_found': arxiv_results is not None,
            'arxiv_results': arxiv_results
        }
        results.append(result)
        
        if arxiv_results:
            found_count += 1
            print(f"  ✅ 找到 {len(arxiv_results)} 个结果")
            if arxiv_results:
                print(f"  arXiv ID: {arxiv_results[0].get('arxiv_id', 'N/A')}")
                print(f"  arXiv URL: {arxiv_results[0].get('url', 'N/A')}")
                pdf_url = arxiv_results[0].get('pdf_url')
                if pdf_url:
                    pdf_available_count += 1
                    print(f"  📄 PDF URL: {pdf_url}")
                else:
                    print(f"  ⚠️  No PDF URL available")
                # 显示分类
                categories = arxiv_results[0].get('categories', [])
                if categories:
                    print(f"  分类: {', '.join(categories[:3])}")  # 只显示前3个分类
        else:
            not_found_count += 1
            print(f"  ❌ 未找到")
        
        print()
        
        # arXiv API 建议: 每次请求间隔 3 秒
        time.sleep(3.1)
    
    # 统计结果
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)
    print(f"采样论文数: {len(sampled_papers)}")
    print(f"找到论文: {found_count} 篇 ({found_count/len(sampled_papers)*100:.1f}%)")
    print(f"未找到: {not_found_count} 篇 ({not_found_count/len(sampled_papers)*100:.1f}%)")
    print(f"有 PDF URL: {pdf_available_count} 篇 ({pdf_available_count/len(sampled_papers)*100:.1f}%)")
    print(f"\narXiv 覆盖率: {found_count/len(sampled_papers)*100:.1f}%")
    print(f"PDF URL 覆盖率: {pdf_available_count/len(sampled_papers)*100:.1f}%")
    
    return results, pdf_available_count


def save_results(results, pdf_available_count, output_file):
    """保存测试结果"""
    # 提取未找到的论文信息
    not_found_papers = []
    for r in results:
        if not r['arxiv_found']:
            not_found_papers.append({
                'title': r['paper'].get('title', ''),
                'author_name': r['paper'].get('author_name', ''),
                'venue': r['paper'].get('venue', ''),
                'year': r['paper'].get('year', ''),
                'citations': r['paper'].get('citations', 0)
            })
    
    summary = {
        'total_tested': len(results),
        'found': sum(1 for r in results if r['arxiv_found']),
        'not_found': sum(1 for r in results if not r['arxiv_found']),
        'pdf_available': pdf_available_count,
        'coverage_rate': sum(1 for r in results if r['arxiv_found']) / len(results) * 100,
        'pdf_coverage_rate': pdf_available_count / len(results) * 100,
        'not_found_papers': not_found_papers,  # 未找到的论文列表
        'detailed_results': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到: {output_file}")
    
    # 单独保存未找到的论文到另一个文件，方便查看
    if not_found_papers:
        not_found_file = output_file.replace('.json', '_not_found.json')
        with open(not_found_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_not_found': len(not_found_papers),
                'not_found_papers': not_found_papers
            }, f, indent=2, ensure_ascii=False)
        print(f"未找到的论文列表已保存到: {not_found_file}")
        print(f"共 {len(not_found_papers)} 篇论文未在 arXiv 上找到")


if __name__ == "__main__":
    # 支持从目录或zip文件读取
    # 如果zip文件存在，优先使用zip文件（更节省空间）
    profiles_zip = "/Users/yuhli/Desktop/citation/crawling_profiles/all_author_profiles.zip"
    profiles_directory = "/Users/yuhli/Desktop/citation/crawling_profiles/all_author_profiles"
    
    # 自动选择：优先使用zip文件，如果不存在则使用目录
    if Path(profiles_zip).exists():
        profiles_source = profiles_zip
        print(f"使用zip文件: {profiles_zip}\n")
    else:
        profiles_source = profiles_directory
        print(f"使用目录: {profiles_directory}\n")
    
    output_filepath = "/Users/yuhli/Desktop/citation/crawling_papers/arxiv_coverage_test.json"
    
    # 步骤1: 收集100个作者的所有论文
    all_papers = collect_all_papers(profiles_source, num_authors=100)
    
    # 步骤2: 随机采样100篇论文测试
    results, pdf_available_count = test_arxiv_coverage(all_papers, sample_size=100)
    
    # 步骤3: 保存结果
    save_results(results, pdf_available_count, output_filepath)

