import json
import numpy as np
from FlagEmbedding import BGEM3FlagModel
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
    
    # 初始化模型
    print("\nLoading BGE-M3 model...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True, devices=['cuda:0'])
    
    # 计算embeddings (分批处理以避免内存问题)
    print("\nComputing embeddings...")
    batch_size = 64
    all_embeddings = []
    
    for i in tqdm(range(0, len(abstracts), batch_size)):
        batch = abstracts[i:i+batch_size]
        embeddings = model.encode(batch, batch_size=batch_size)['dense_vecs']
        all_embeddings.append(embeddings)
    
    # 合并所有embeddings
    all_embeddings = np.vstack(all_embeddings)
    print(f"\nEmbeddings shape: {all_embeddings.shape}")
    
    # 保存到 /mnt/localssd
    output_dir = '/mnt/localssd'
    os.makedirs(output_dir, exist_ok=True)
    
    embeddings_path = os.path.join(output_dir, 'paper_embeddings.npy')
    metadata_path = os.path.join(output_dir, 'paper_metadata.json')
    
    print(f"\nSaving embeddings to {embeddings_path}...")
    np.save(embeddings_path, all_embeddings)
    
    print(f"Saving metadata to {metadata_path}...")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n✓ Done!")
    print(f"  - Embeddings: {embeddings_path} ({all_embeddings.shape})")
    print(f"  - Metadata: {metadata_path} ({len(metadata)} papers)")


