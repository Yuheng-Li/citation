#!/usr/bin/env python3
"""
测试 Semantic Scholar 覆盖率：随机采样 100 篇论文，看能找到多少
"""
import json
import random
import time
from pathlib import Path
import requests
import sys

# 添加父目录到路径，以便导入profile_reader
sys.path.append(str(Path(__file__).parent.parent))
from crawling_profiles.profile_reader import collect_all_papers


def search_semantic_scholar(title, author=None):
    """
    使用 Semantic Scholar API 搜索论文
    API 文档: https://api.semanticscholar.org/
    """
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    # API Key (1 request per second)
    API_KEY = "78q8LRUz2IZgHoDiPvH42MVb0vEmR7p4mpiXZ0Ej"
    
    # 构建查询
    if author:
        query = f'{title} {author}'
    else:
        query = title
    
    params = {
        'query': query,
        'limit': 3,  # 最多返回3个结果
        'fields': 'paperId,title,authors,year,venue,citationCount,abstract,url,publicationTypes,openAccessPdf,externalIds'
    }
    
    headers = {
        "x-api-key": API_KEY,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            papers = data.get('data', [])
            
            if not papers:
                return None
            
            results = []
            for paper in papers:
                # 获取 PDF URL
                pdf_url = None
                external_ids = paper.get('externalIds', {})
                
                # 优先使用开放获取 PDF
                if paper.get('openAccessPdf') and paper.get('openAccessPdf', {}).get('url'):
                    pdf_url = paper.get('openAccessPdf', {}).get('url')
                # 如果有 arXiv ID，构建 arXiv PDF URL
                elif external_ids and external_ids.get('ArXiv'):
                    arxiv_id = external_ids.get('ArXiv')
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                result = {
                    'paper_id': paper.get('paperId'),
                    'title': paper.get('title'),
                    'authors': [a.get('name') for a in paper.get('authors', [])],
                    'year': paper.get('year'),
                    'venue': paper.get('venue'),
                    'citation_count': paper.get('citationCount'),
                    'abstract': paper.get('abstract'),
                    'url': paper.get('url'),
                    'publication_types': paper.get('publicationTypes', []),
                    'pdf_url': pdf_url,  # 可以 wget 的 PDF URL
                    'external_ids': external_ids,  # DOI, arXiv ID, PubMed ID 等
                    'open_access': paper.get('openAccessPdf')
                }
                results.append(result)
            
            return results
            
        elif response.status_code == 429:
            print(f"  ⚠️  Rate limit exceeded, waiting...")
            time.sleep(60)  # 等待1分钟
            return search_semantic_scholar(title, author)  # 重试
        else:
            print(f"  ⚠️  HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return None


# collect_all_papers 函数已移至 profile_reader.py，现在直接导入使用


def test_semantic_scholar_coverage(all_papers, sample_size=100):
    """测试 Semantic Scholar 覆盖率"""
    # 随机打乱并采样
    random.shuffle(all_papers)
    sampled_papers = all_papers[:sample_size]
    
    print(f"\n随机采样 {len(sampled_papers)} 篇论文进行测试\n")
    print("=" * 80)
    
    found_count = 0
    not_found_count = 0
    pdf_available_count = 0  # 有 PDF URL 的数量
    
    results = []
    
    for idx, paper in enumerate(sampled_papers, 1):
        title = paper['title']
        author = paper['author_name']
        
        print(f"[{idx}/{len(sampled_papers)}] 搜索: {title[:60]}...")
        print(f"  作者: {author}")
        
        s2_results = search_semantic_scholar(title, author=author)
        
        result = {
            'paper': paper,
            's2_found': s2_results is not None,
            's2_results': s2_results
        }
        results.append(result)
        
        if s2_results:
            found_count += 1
            print(f"  ✅ 找到 {len(s2_results)} 个结果")
            if s2_results:
                print(f"  S2 Paper ID: {s2_results[0].get('paper_id', 'N/A')}")
                print(f"  S2 URL: {s2_results[0].get('url', 'N/A')}")
                pdf_url = s2_results[0].get('pdf_url')
                if pdf_url:
                    pdf_available_count += 1
                    print(f"  📄 PDF URL: {pdf_url}")
                else:
                    print(f"  ⚠️  No PDF URL available")
        else:
            not_found_count += 1
            print(f"  ❌ 未找到")
        
        print()
        
        # Semantic Scholar API 限制 (with API key): 1 request per second
        time.sleep(1.1)
    
    # 统计结果
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)
    print(f"采样论文数: {len(sampled_papers)}")
    print(f"找到论文: {found_count} 篇 ({found_count/len(sampled_papers)*100:.1f}%)")
    print(f"未找到: {not_found_count} 篇 ({not_found_count/len(sampled_papers)*100:.1f}%)")
    print(f"有 PDF URL: {pdf_available_count} 篇 ({pdf_available_count/len(sampled_papers)*100:.1f}%)")
    print(f"\nSemantic Scholar 覆盖率: {found_count/len(sampled_papers)*100:.1f}%")
    print(f"PDF URL 覆盖率: {pdf_available_count/len(sampled_papers)*100:.1f}%")
    
    return results, pdf_available_count


def save_results(results, pdf_available_count, output_file):
    """保存测试结果"""
    # 提取未找到的论文信息
    not_found_papers = []
    for r in results:
        if not r['s2_found']:
            not_found_papers.append({
                'title': r['paper'].get('title', ''),
                'author_name': r['paper'].get('author_name', ''),
                'venue': r['paper'].get('venue', ''),
                'year': r['paper'].get('year', ''),
                'citations': r['paper'].get('citations', 0)
            })
    
    summary = {
        'total_tested': len(results),
        'found': sum(1 for r in results if r['s2_found']),
        'not_found': sum(1 for r in results if not r['s2_found']),
        'pdf_available': pdf_available_count,
        'coverage_rate': sum(1 for r in results if r['s2_found']) / len(results) * 100,
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
        print(f"共 {len(not_found_papers)} 篇论文未在 Semantic Scholar 上找到")


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
    
    output_filepath = "/Users/yuhli/Desktop/citation/crawling_papers/semantic_scholar_coverage_test.json"
    
    # 步骤1: 收集100个作者的所有论文
    all_papers = collect_all_papers(profiles_source, num_authors=100)
    
    # 步骤2: 随机采样100篇论文测试
    results, pdf_available_count = test_semantic_scholar_coverage(all_papers, sample_size=100)
    
    # 步骤3: 保存结果
    save_results(results, pdf_available_count, output_filepath)

