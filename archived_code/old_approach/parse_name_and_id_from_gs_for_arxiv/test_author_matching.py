#!/usr/bin/env python3
"""
测试 gs_data_collection.json 中的作者匹配情况
比较 gs_authors 和 arxiv_authors 是否匹配
"""
import json
from name_matcher import match_author_names


def test_author_matching(json_file="gs_data_collection.json"):
    """
    测试作者匹配情况
    
    Args:
        json_file: JSON 文件路径
    """
    print(f"加载数据: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    print(f"总论文数: {len(papers)}\n")
    print("=" * 80)
    
    results = []
    total_matches = 0
    total_comparisons = 0
    
    for idx, paper in enumerate(papers, 1):
        arxiv_id = paper.get('arxiv_id', 'N/A')
        arxiv_authors = paper.get('arxiv_authors', [])
        gs_authors = paper.get('gs_authors', [])
        gs_search_success = paper.get('gs_search_success', False)
        
        # 只处理成功获取 GS 数据的论文
        if not gs_search_success or not gs_authors:
            continue
        
        # 确定要比较的作者数量：前 len(gs_authors) - 1 个
        num_to_compare = len(gs_authors) - 1
        if num_to_compare <= 0:
            # 如果只有1个或0个作者，跳过
            continue
        
        # 确保不超过 arxiv_authors 的数量
        num_to_compare = min(num_to_compare, len(arxiv_authors))
        
        if num_to_compare <= 0:
            continue
        
        # 进行比较
        matches = 0
        match_details = []
        
        for i in range(num_to_compare):
            arxiv_name = arxiv_authors[i]
            gs_name = gs_authors[i].get('name', '') if isinstance(gs_authors[i], dict) else str(gs_authors[i])
            
            is_match = match_author_names(arxiv_name, gs_name)
            
            if is_match:
                matches += 1
                match_details.append(f"✅ {arxiv_name} <-> {gs_name}")
            else:
                match_details.append(f"❌ {arxiv_name} <-> {gs_name}")
        
        match_ratio = f"{matches}/{num_to_compare}"
        total_matches += matches
        total_comparisons += num_to_compare
        
        result = {
            'arxiv_id': arxiv_id,
            'title': paper.get('title', '')[:60] + '...' if len(paper.get('title', '')) > 60 else paper.get('title', ''),
            'arxiv_count': len(arxiv_authors),
            'gs_count': len(gs_authors),
            'compared_count': num_to_compare,
            'matches': matches,
            'match_ratio': match_ratio,
            'match_details': match_details
        }
        results.append(result)
        
        # 打印每篇论文的结果
        print(f"[{idx}] arXiv ID: {arxiv_id}")
        print(f"    标题: {result['title']}")
        print(f"    arXiv 作者数: {len(arxiv_authors)}, GS 作者数: {len(gs_authors)}")
        print(f"    匹配: {match_ratio} ({matches}/{num_to_compare})")
        if matches < num_to_compare:
            print(f"    不匹配的作者:")
            for detail in match_details:
                if '❌' in detail:
                    print(f"      {detail}")
        print()
    
    # 打印总体统计
    print("=" * 80)
    print("总体统计")
    print("=" * 80)
    print(f"成功获取 GS 数据的论文数: {len(results)}")
    print(f"总比较次数: {total_comparisons}")
    print(f"总匹配次数: {total_matches}")
    if total_comparisons > 0:
        match_rate = (total_matches / total_comparisons) * 100
        print(f"总体匹配率: {match_rate:.2f}%")
    
    # 按匹配率分组统计
    print("\n按匹配率分组:")
    perfect_matches = [r for r in results if r['matches'] == r['compared_count']]
    partial_matches = [r for r in results if 0 < r['matches'] < r['compared_count']]
    no_matches = [r for r in results if r['matches'] == 0]
    
    print(f"  完全匹配 ({len(perfect_matches)} 篇): 所有比较的作者都匹配")
    print(f"  部分匹配 ({len(partial_matches)} 篇): 部分作者匹配")
    print(f"  无匹配 ({len(no_matches)} 篇): 没有作者匹配")
    
    # 显示一些不匹配的例子
    if partial_matches or no_matches:
        print("\n不匹配的例子（前5个）:")
        examples = (partial_matches + no_matches)[:5]
        for ex in examples:
            print(f"  arXiv ID: {ex['arxiv_id']}")
            print(f"    匹配: {ex['match_ratio']}")
            for detail in ex['match_details']:
                if '❌' in detail:
                    print(f"    {detail}")
            print()
    
    # 保存部分匹配和无匹配的论文到 JSON 文件
    mismatched_papers = partial_matches + no_matches
    if mismatched_papers:
        output_file = "mismatched_authors.json"
        # 为了保存完整信息，需要从原始数据中获取完整论文信息
        with open("gs_data_collection.json", 'r', encoding='utf-8') as f:
            all_papers_data = json.load(f)
        
        # 创建 arxiv_id 到论文的映射
        papers_dict = {p.get('arxiv_id'): p for p in all_papers_data}
        
        # 构建要保存的数据
        output_data = []
        for result in mismatched_papers:
            arxiv_id = result['arxiv_id']
            if arxiv_id in papers_dict:
                paper_data = papers_dict[arxiv_id].copy()
                # 添加匹配分析信息
                paper_data['match_analysis'] = {
                    'match_ratio': result['match_ratio'],
                    'matches': result['matches'],
                    'compared_count': result['compared_count'],
                    'arxiv_count': result['arxiv_count'],
                    'gs_count': result['gs_count'],
                    'match_details': result['match_details']
                }
                output_data.append(paper_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n部分匹配和无匹配的论文已保存到: {output_file}")
        print(f"共 {len(output_data)} 篇论文")
    
    return results


if __name__ == "__main__":
    results = test_author_matching()

