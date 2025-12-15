import requests
import json

API_BASE = "https://api.semanticscholar.org/graph/v1"
API_KEY = "78q8LRUz2IZgHoDiPvH42MVb0vEmR7p4mpiXZ0Ej"

def search_paper(title):
    """搜索论文"""
    url = f"{API_BASE}/paper/search"
    params = {
        "query": title,
        "limit": 1,
        "fields": "paperId,title,year,citationCount,authors"
    }
    headers = {"x-api-key": API_KEY}
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    if data.get("data") and len(data["data"]) > 0:
        return data["data"][0]
    return None

def get_citations(paper_id, limit=100):
    """获取引用这篇论文的文章"""
    url = f"{API_BASE}/paper/{paper_id}/citations"
    params = {
        "fields": "title,year,citationCount,authors,venue",
        "limit": limit
    }
    headers = {"x-api-key": API_KEY}
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    return response.json()

def main():
    target_title = "Dynamic Graph CNN for Learning on Point Clouds"
    
    print("="*80)
    print(f"Searching for: {target_title}")
    print("="*80)
    
    # 搜索论文
    paper = search_paper(target_title)
    
    if not paper:
        print("❌ Paper not found!")
        return
    
    print(f"\n✅ Found paper:")
    print(f"   Title: {paper['title']}")
    print(f"   Year: {paper.get('year', 'N/A')}")
    print(f"   Paper ID: {paper['paperId']}")
    print(f"   Citation Count: {paper.get('citationCount', 0)}")
    print(f"   Authors: {', '.join([a.get('name', 'Unknown') for a in paper.get('authors', [])])}")
    
    # 获取引用
    print(f"\n{'='*80}")
    print(f"Fetching citations (showing top 100)...")
    print(f"{'='*80}\n")
    
    citations_data = get_citations(paper['paperId'], limit=100)
    citations = citations_data.get('data', [])
    
    if not citations:
        print("No citations found.")
        return
    
    print(f"Total citations available: {len(citations)}")
    print(f"\nTop citing papers:\n")
    
    for i, cite in enumerate(citations, 1):
        citing_paper = cite.get('citingPaper', {})
        title = citing_paper.get('title', 'No title')
        year = citing_paper.get('year', 'N/A')
        venue = citing_paper.get('venue', 'N/A')
        cite_count = citing_paper.get('citationCount', 0)
        authors = citing_paper.get('authors', [])
        author_names = ', '.join([a.get('name', '') for a in authors[:3]])
        if len(authors) > 3:
            author_names += f" et al. ({len(authors)} authors)"
        
        print(f"[{i}] {title}")
        print(f"    Year: {year} | Venue: {venue} | Citations: {cite_count}")
        print(f"    Authors: {author_names}")
        print()
    
    # 保存到文件
    output_file = "citations_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'target_paper': paper,
            'citations': citations,
            'total_count': len(citations)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Full results saved to: {output_file}")

if __name__ == "__main__":
    main()

