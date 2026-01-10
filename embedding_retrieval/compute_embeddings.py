import json
import numpy as np
from openai import OpenAI
from tqdm import tqdm
import os

if __name__ == '__main__':
    # 加载数据
    print("Loading papers...")
    with open('../cv_papers_20230101_to_20250531.json', 'r') as f:
        papers = json.load(f)
    
    print(f"Total papers: {len(papers)}")
    
    # 提取所有abstracts和metadata
    abstracts = []
    metadata = []
    
    for paper in papers:
        abstract = paper.get('abstract', '')
        if abstract:  # 只处理有abstract的paper
            abstracts.append(abstract)
            metadata.append({
                'arxiv_id': paper['arxiv_id'],
                'title': paper['title'],
                'authors': paper['authors'],
                'year': paper['year'],
                'categories': paper['categories']
            })
    
    print(f"Papers with abstracts: {len(abstracts)}")
    
    # 初始化OpenAI客户端
    print("\nInitializing OpenAI client...")
    endpoint = "http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000"
    api_key = "sk-2CtQupQUahmV2nXHAXjUxg"
    
    client = OpenAI(
        api_key="Bearer " + api_key,
        base_url=endpoint,
    )
    
    # 计算embeddings (分批处理以避免内存问题)
    print("\nComputing embeddings with OpenAI text-embedding-3-small...")
    batch_size = 100  # OpenAI可以处理更大的batch
    all_embeddings = []
    
    for i in tqdm(range(0, len(abstracts), batch_size)):
        batch = abstracts[i:i+batch_size]
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
    
    # 转换为numpy数组
    all_embeddings = np.array(all_embeddings)
    print(f"\nEmbeddings shape: {all_embeddings.shape}")
    
    # 保存到独立文件夹
    output_dir = '/mnt/localssd/paper_embeddings'
    os.makedirs(output_dir, exist_ok=True)
    
    embeddings_path = os.path.join(output_dir, 'paper_embeddings.npy')
    metadata_path = os.path.join(output_dir, 'paper_metadata.json')
    id_to_idx_path = os.path.join(output_dir, 'arxiv_id_to_idx.json')
    
    print(f"\nSaving embeddings to {embeddings_path}...")
    np.save(embeddings_path, all_embeddings)
    
    print(f"Saving metadata to {metadata_path}...")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # 保存 arxiv_id -> index 映射
    print(f"Saving ID mapping to {id_to_idx_path}...")
    id_to_idx = {meta['arxiv_id']: i for i, meta in enumerate(metadata)}
    with open(id_to_idx_path, 'w') as f:
        json.dump(id_to_idx, f, indent=2)
    
    print("\n✓ Done!")
    print(f"  - Embeddings: {embeddings_path} ({all_embeddings.shape})")
    print(f"  - Metadata: {metadata_path} ({len(metadata)} papers)")
    print(f"  - ID Mapping: {id_to_idx_path} ({len(id_to_idx)} IDs)")


