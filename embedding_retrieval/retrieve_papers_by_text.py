import json
import numpy as np
from openai import OpenAI

def retrieve_papers_by_text(query_text, top_k=10):
    """
    根据文本描述检索最相关的论文
    
    Args:
        query_text: 描述研究兴趣/方向的文本
        top_k: 返回前k个最相关的论文
    
    Returns:
        list of dict: 包含论文信息和相似度的列表
    """
    # 初始化OpenAI客户端
    print("Initializing OpenAI client...")
    endpoint = "http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000"
    api_key = "sk-2CtQupQUahmV2nXHAXjUxg"
    
    client = OpenAI(
        api_key="Bearer " + api_key,
        base_url=endpoint,
    )
    
    # 对query文本进行embedding
    print(f"Encoding query text...")
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query_text
    )
    query_embedding = np.array(response.data[0].embedding)
    
    # 加载论文embeddings
    print("Loading paper embeddings...")
    embeddings = np.load('/mnt/localssd/paper_embeddings/paper_embeddings.npy')
    
    with open('/mnt/localssd/paper_embeddings/paper_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    # 计算cosine similarity
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    similarities = np.dot(embeddings_norm, query_norm)
    
    # 获取top k
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        paper_meta = metadata[idx]
        results.append({
            'arxiv_id': paper_meta['arxiv_id'],
            'title': paper_meta['title'],
            'authors': paper_meta['authors'],
            'year': paper_meta['year'],
            'categories': paper_meta['categories'],
            'similarity': float(similarities[idx])
        })
    
    return results


if __name__ == '__main__':
    # 示例：根据研究方向描述检索论文
    query_text = """
    personalization on multimodal LLMs, personalized understanding.
    """
    
    print(f"\nQuery text:")
    print(f'"{query_text.strip()}"')
    print("\n" + "=" * 80)
    
    results = retrieve_papers_by_text(query_text, top_k=10)
    
    print(f"\nTop 10 most relevant papers:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   arXiv ID: {result['arxiv_id']}")
        print(f"   Authors: {', '.join(result['authors'][:3])}{'...' if len(result['authors']) > 3 else ''}")
        print(f"   Year: {result['year']}")
        print(f"   Similarity: {result['similarity']:.4f}")
        print()

