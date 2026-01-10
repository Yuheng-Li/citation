import json
import zipfile
from collections import defaultdict

print("📂 第1步: 读取所有作者档案...")
author_names = {}  # author_id -> name
zip_path = 'crawling_profiles/all_author_profiles_cv.zip'

with zipfile.ZipFile(zip_path, 'r') as zip_file:
    file_list = zip_file.namelist()
    total_authors = len(file_list)
    
    for idx, filename in enumerate(file_list):
        if idx % 5000 == 0:
            print(f"  处理中... {idx}/{total_authors}")
        
        # 提取作者 ID (从 author_XXX.json 中提取 XXX)
        if filename.startswith('author_') and filename.endswith('.json'):
            author_id = filename[7:-5]  # 去掉 'author_' 和 '.json'
            
            # 读取 JSON 获取作者姓名
            with zip_file.open(filename) as f:
                try:
                    profile = json.load(f)
                    name = profile.get('author_info', {}).get('name', 'Unknown')
                    author_names[author_id] = name
                except:
                    author_names[author_id] = 'Unknown'

print(f"✅ 读取了 {len(author_names)} 个作者档案")

print("\n📄 第2步: 读取论文数据并构建映射...")
with open('gs_data_collection.json', 'r') as f:
    papers = json.load(f)

# 构建结果字典
author_papers = {}
for author_id, name in author_names.items():
    author_papers[author_id] = {
        "name": name,
        "papers": []
    }

# 遍历所有论文，将论文添加到对应作者
paper_count = 0
for idx, paper in enumerate(papers):
    if idx % 10000 == 0:
        print(f"  处理论文... {idx}/{len(papers)}")
    
    arxiv_id = paper.get('arxiv_id')
    title = paper.get('title', 'Unknown')
    gs_authors = paper.get('gs_authors', [])
    
    if arxiv_id and gs_authors:
        paper_info = {
            'arxiv_id': arxiv_id,
            'title': title
        }
        for author_id in gs_authors:
            if author_id in author_papers:
                author_papers[author_id]['papers'].append(paper_info)
                paper_count += 1

print(f"✅ 处理了 {len(papers)} 篇论文，建立了 {paper_count} 个作者-论文关联")

print("\n💾 第3步: 保存结果...")
with open('author_to_papers.json', 'w') as f:
    json.dump(author_papers, f, indent=2, ensure_ascii=False)

# 统计信息
authors_with_papers = sum(1 for v in author_papers.values() if len(v['papers']) > 0)
total_paper_links = sum(len(v['papers']) for v in author_papers.values())

print(f"\n📊 统计:")
print(f"- 总作者数: {len(author_papers)}")
print(f"- 有论文的作者数: {authors_with_papers}")
print(f"- 无论文的作者数: {len(author_papers) - authors_with_papers}")
print(f"- 总作者-论文关联数: {total_paper_links}")
print(f"\n✅ 结果已保存到: author_to_papers.json")

