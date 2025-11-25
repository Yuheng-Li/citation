#!/usr/bin/env python3
"""
优化版本：使用贪心算法找到最小的论文集合
目标：覆盖所有 active_authors.json 中定义的活跃作者
"""

import os
import json
import time

def main():
    print("="*80)
    print("最小论文集合查找 - 基于活跃作者")
    print("="*80)
    print("目标：覆盖所有 active_authors.json 中的活跃作者")
    print("="*80)
    print()
    
    start_time = time.time()
    
    # 1. 加载活跃作者
    print("步骤 1: 加载活跃作者...")
    active_authors_file = 'active_authors.json'
    
    if not os.path.exists(active_authors_file):
        print(f"错误: 文件 '{active_authors_file}' 不存在！")
        print("请先运行 analyze_active_authors.py 生成活跃作者列表。")
        return
    
    with open(active_authors_file, 'r', encoding='utf-8') as f:
        active_authors_data = json.load(f)
    
    target_authors = {author['name'] for author in active_authors_data}
    print(f"✓ 加载了 {len(target_authors):,} 位活跃作者 ({time.time()-start_time:.1f}s)\n")
    
    # 2. 加载所有论文
    print("步骤 2: 加载所有论文...")
    step_start = time.time()
    folder = 'conference_papers'
    
    if not os.path.exists(folder):
        print(f"错误: 文件夹 '{folder}' 不存在！")
        return
    
    all_papers = []
    files = sorted([f for f in os.listdir(folder) if f.endswith('.json')])
    
    if not files:
        print(f"错误: 在 '{folder}' 中没有找到JSON文件！")
        return
    
    for filename in files:
        filepath = os.path.join(folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                papers = json.load(f)
                for paper in papers:
                    paper['source_file'] = filename
                all_papers.extend(papers)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"警告: 跳过文件 {filename}, 错误: {e}")
            continue
    
    print(f"✓ 加载了 {len(all_papers):,} 篇论文 ({time.time()-step_start:.1f}s)\n")
    
    # 3. 预处理：只保留包含目标作者的论文
    print("步骤 3: 预处理论文...")
    step_start = time.time()
    relevant_papers = []
    for i, paper in enumerate(all_papers):
        if i % 5000 == 0:
            print(f"  处理中: {i:,}/{len(all_papers):,}", end='\r', flush=True)
        
        # 清理作者名字，去除空值
        authors = set()
        for author in paper.get('authors', []):
            if author and str(author).strip():
                authors.add(str(author).strip())
        
        # 只保留至少有一个目标作者的论文
        if authors & target_authors:
            paper['target_authors'] = authors & target_authors
            relevant_papers.append(paper)
    
    print(f"\r✓ 过滤到 {len(relevant_papers):,} 篇相关论文 ({time.time()-step_start:.1f}s)")
    print(f"  减少了 {len(all_papers) - len(relevant_papers):,} 篇 ({(1-len(relevant_papers)/len(all_papers))*100:.1f}%)\n")
    
    # 4. 贪心算法  
    print("步骤 4: 运行贪心算法...")
    print("-"*80)
    
    uncovered = target_authors.copy()
    selected = []
    iteration = 0
    algo_start = time.time()
    
    while uncovered and relevant_papers:
        iteration += 1
        iter_start = time.time()
        
        # 找到覆盖最多未覆盖作者的论文
        best_idx = -1
        best_count = 0
        
        print(f"  第 {iteration:4d} 轮: 检查 {len(relevant_papers):,} 篇论文...", end='', flush=True)
        
        for i, paper in enumerate(relevant_papers):
            # 每5000篇打印进度
            if i > 0 and i % 5000 == 0:
                print(f"\r  第 {iteration:4d} 轮: 检查中 {i:,}/{len(relevant_papers):,}...", end='', flush=True)
            
            count = len(paper['target_authors'] & uncovered)
            if count > best_count:
                best_count = count
                best_idx = i
        
        if best_idx == -1 or best_count == 0:
            print("\r✗ 无法找到更多覆盖")
            break
        
        # 选择最佳论文
        best_paper = relevant_papers.pop(best_idx)
        selected.append(best_paper)
        uncovered -= best_paper['target_authors']
        
        # 优化：移除不再能覆盖任何未覆盖作者的论文
        if iteration % 10 == 0:  # 每10轮清理一次，避免每轮都清理影响性能
            relevant_papers = [p for p in relevant_papers if p['target_authors'] & uncovered]
        
        coverage_pct = (len(target_authors) - len(uncovered)) / len(target_authors) * 100
        iter_time = time.time() - iter_start
        
        print(f"\r  第 {iteration:4d} 轮: 覆盖 {len(target_authors)-len(uncovered):6,}/{len(target_authors):,} "
              f"({coverage_pct:5.1f}%), 新增 {best_count:3d} 位, "
              f"已选 {len(selected):4,} 篇, 用时 {iter_time:.1f}s")
        
        # 如果覆盖率超过99.5%，可以考虑提前结束
        if coverage_pct >= 99.5:
            print(f"\n  ℹ️  已覆盖 {coverage_pct:.2f}%，接近完成")
    
    print("-"*80)
    print(f"✓ 算法完成，用时 {time.time()-algo_start:.1f}s\n")
    
    # 5. 验证
    print("步骤 5: 验证覆盖...")
    covered = set()
    for paper in selected:
        covered.update(paper.get('authors', []))
    
    coverage = len(covered & target_authors)
    print(f"✓ 覆盖了 {coverage:,} / {len(target_authors):,} 位目标作者")
    print(f"✓ 覆盖率: {coverage / len(target_authors) * 100:.2f}%\n")
    
    # 6. 保存结果
    print("步骤 6: 保存结果...")
    
    # 清理论文数据（移除临时字段）
    for paper in selected:
        if 'target_authors' in paper:
            del paper['target_authors']
    
    # 保存JSON
    with open('minimal_paper_set.json', 'w', encoding='utf-8') as f:
        json.dump(selected, f, indent=2, ensure_ascii=False)
    print(f"✓ 论文集合已保存到: minimal_paper_set.json")
    
    # 保存报告
    with open('minimal_paper_set_report.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("最小论文集合 - 基于活跃作者的贪心算法结果\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"总论文数: {len(all_papers):,}\n")
        f.write(f"目标作者数（来自 active_authors.json）: {len(target_authors):,}\n")
        f.write(f"选中的论文数: {len(selected):,}\n")
        f.write(f"压缩比: {len(selected) / len(all_papers) * 100:.2f}%\n")
        f.write(f"覆盖的作者数: {coverage:,}\n")
        f.write(f"覆盖率: {coverage / len(target_authors) * 100:.2f}%\n")
        f.write(f"总用时: {time.time() - start_time:.1f} 秒\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("选中的论文列表\n")
        f.write("="*80 + "\n\n")
        
        for i, paper in enumerate(selected, 1):
            f.write(f"{i}. {paper['title']}\n")
            f.write(f"   来源: {paper.get('venue', 'N/A')}\n")
            authors = paper.get('authors', [])
            f.write(f"   作者 ({len(authors)}): {', '.join(authors[:5])}")
            if len(authors) > 5:
                f.write(f" ... 等 {len(authors) - 5} 位")
            f.write("\n\n")
    
    print(f"✓ 详细报告已保存到: minimal_paper_set_report.txt")
    
    # 最终统计
    print("\n" + "="*80)
    print("最终统计")
    print("="*80)
    print(f"原始论文数:     {len(all_papers):6,} 篇")
    print(f"最小论文集合:   {len(selected):6,} 篇")
    print(f"压缩比:         {len(selected) / len(all_papers) * 100:6.2f}%")
    print(f"节省:           {len(all_papers) - len(selected):6,} 篇 ({(1 - len(selected) / len(all_papers)) * 100:.2f}%)")
    print(f"总用时:         {time.time() - start_time:6.1f} 秒")
    print()
    print(f"🎉 你只需要处理 {len(selected):,} 篇论文，而不是 {len(all_papers):,} 篇！")
    print(f"💰 这将节省 {(1 - len(selected) / len(all_papers)) * 100:.1f}% 的计算时间！")


if __name__ == '__main__':
    main()

