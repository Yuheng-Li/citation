import json
import time
import requests
from typing import List, Dict, Set

# Semantic Scholar API配置
API_BASE = "https://api.semanticscholar.org/graph/v1"
# API Key (1 request per second)
API_KEY = "78q8LRUz2IZgHoDiPvH42MVb0vEmR7p4mpiXZ0Ej"

def search_paper(title: str) -> Dict:
    """通过标题搜索论文"""
    url = f"{API_BASE}/paper/search"
    params = {
        "query": title,
        "limit": 1,
        "fields": "paperId,title,authors"
    }
    headers = {
        "x-api-key": API_KEY,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    breakpoint()
    if data.get("data") and len(data["data"]) > 0:
        return data["data"][0]
    return None

def extract_author_ids(paper: Dict) -> List[str]:
    """从论文数据中提取作者ID"""
    if not paper or "authors" not in paper:
        return []
    
    author_ids = []
    for author in paper["authors"]:
        if "authorId" in author and author["authorId"]:
            author_ids.append(author["authorId"])
    
    return author_ids

def save_progress(results: Dict, all_ids: Set, output_dir: str = "google"):
    """保存进度"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存详细结果
    with open(f"{output_dir}/semantic_scholar_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 保存所有唯一的作者ID
    with open(f"{output_dir}/semantic_scholar_author_ids.txt", "w", encoding="utf-8") as f:
        for author_id in sorted(all_ids):
            f.write(author_id + "\n")
    
    print(f"  💾 Progress saved: {len(results)} papers, {len(all_ids)} unique authors")




def main():

    

    print(" - - - - - - - - - - - - - - Loading paper titles - - - - - - - - - - - - - -")
    with open("google/cvpr_titles.json", "r", encoding="utf-8") as f:
        titles = json.load(f)
    print(f"   Total: {len(titles)} papers")
    



    print(" - - - - - - - - - - - - - - Checking for existing progress - - - - - - - - - - - - - -")
    results = {}
    all_author_ids = set()
    
    try:
        with open("google/semantic_scholar_results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
        with open("google/semantic_scholar_author_ids.txt", "r", encoding="utf-8") as f:
            all_author_ids = set(line.strip() for line in f if line.strip())
        print(f"   ✓ Found: {len(results)} processed, {len(all_author_ids)} unique authors")
    except FileNotFoundError:
        print("   No existing progress found, starting fresh")
    
    remaining_titles = [t for t in titles if t not in results]
    print(f"   Remaining: {len(remaining_titles)} papers")
    
    if not remaining_titles:
        print("\n✅ All papers have been processed!")
        return
    

    print(f" - - - - - - - - - - - - - - Starting extraction - - - - - - - - - - - - - -")
    print(f"   API Rate: 1 request/second")
    print(f"   Estimated time: ~{len(remaining_titles) * 1.1 / 3600:.1f} hours")
    print()
    
    # 统计
    success_count = 0
    no_result_count = 0
    error_count = 0
    
    for i, title in enumerate(remaining_titles):
        print(f"[{i+1}/{len(remaining_titles)}] {title[:70]}...")
        
        try:
            paper = search_paper(title)
            
            if paper:
                author_ids = extract_author_ids(paper)
                
                if author_ids:
                    results[title] = author_ids
                    all_author_ids.update(author_ids)
                    print(f"   ✓ Found {len(author_ids)} authors: {author_ids[:3]}{'...' if len(author_ids) > 3 else ''}")
                    success_count += 1
                else:
                    results[title] = []
                    print(f"   ⚠️  Paper found but no author IDs")
                    no_result_count += 1
            else:
                results[title] = []
                print(f"   ⚠️  Paper not found")
                no_result_count += 1
            
            if (i + 1) % 10 == 0:
                save_progress(results, all_author_ids)
            

            time.sleep(1.1)
            
        except requests.exceptions.HTTPError as e:
            error_count += 1
            if e.response.status_code == 429:
                print(f"   ⏰ Rate limit hit, waiting 10 seconds...")
                time.sleep(10)
            else:
                print(f"   ❌ HTTP Error: {e}")
                time.sleep(5)
            continue
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ Error: {e}")
            time.sleep(5)
            continue
    
    # 最终保存
    save_progress(results, all_author_ids)
    
    print("\n" + "="*60)
    print("✅ Extraction Complete!")
    print(f"   Success: {success_count}")
    print(f"   No result: {no_result_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total unique authors: {len(all_author_ids)}")
    print("="*60)

if __name__ == "__main__":
    main()

