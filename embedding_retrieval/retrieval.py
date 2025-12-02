import numpy as np
import json
from FlagEmbedding import BGEM3FlagModel

if __name__ == '__main__':
    # 加载保存的embeddings和metadata
    print("Loading embeddings and metadata...")
    paper_embeddings = np.load('/mnt/localssd/paper_embeddings.npy')
    with open('/mnt/localssd/paper_metadata.json', 'r') as f:
        paper_metadata = json.load(f)
    
    print(f"Loaded {len(paper_metadata)} papers with embeddings shape {paper_embeddings.shape}")
    
    # 加载模型
    print("\nLoading BGE-M3 model...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True, devices=['cuda:0'])
    
    # 输入query (可以是paper的abstract或任何文本)
    query = """
While Large Multimodal Models (LMMs) can process diverse visual and textual inputs, they often lack the ability to reason about user-specific or context-specific entities. For instance, a model may describe a generic landscape accurately, but cannot recognize a user’s favorite café or their own artwork. Humans, by contrast, naturally incorporate personal context when interpreting scenes or answering questions. To address this gap, we propose PersoLens, a method that enables LMMs to internalize personalized subjects through a small set of example images. By mapping these examples into a compact latent representation, PersoLens allows the model to generate nuanced, context-aware responses about the subject, such as describing the style of a friend’s painting or recalling a specific object in one’s home. Experiments show that PersoLens captures subject-specific visual details more effectively and efficiently than standard prompting strategies, paving the way for truly personalized multimodal reasoning.
   
    """
    
    print("\nQuery abstract:")
    print(query.strip())
    
    # 计算query的embedding
    print("\nComputing query embedding...")
    query_embedding = model.encode([query])['dense_vecs'][0]  # shape: (1024,)
    
    # 计算相似度 (cosine similarity via dot product, embeddings are normalized)
    print("Computing similarities...")
    similarities = paper_embeddings @ query_embedding  # shape: (69149,)
    
    # 获取top-k最相似的论文
    top_k = 10
    top_indices = np.argsort(similarities)[::-1][:top_k]  # 降序排列，取前k个
    
    print(f"\n{'='*80}")
    print(f"Top {top_k} most similar papers:")
    print(f"{'='*80}\n")
    
    for rank, idx in enumerate(top_indices, 1):
        paper = paper_metadata[idx]
        score = similarities[idx]
        
        print(f"Rank {rank}: (Similarity: {score:.4f})")
        print(f"  ArXiv ID: {paper['arxiv_id']}")
        print(f"  Title: {paper['title']}")
        print(f"  Authors: {', '.join(paper['authors'][:3])}" + 
              (f" et al." if len(paper['authors']) > 3 else ""))
        print(f"  Year: {paper['year']}")
        print(f"  Categories: {', '.join(paper['categories'])}")
        print()

