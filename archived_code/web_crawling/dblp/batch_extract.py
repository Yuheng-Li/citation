import requests
import time
import json
import random
from urllib.parse import quote_plus
from difflib import SequenceMatcher

def search_dblp(title, max_results=1000):
    """Search DBLP for a paper by title using exact phrase matching
    
    Note: max_results set to 1000 because DBLP returns papers containing the phrase,
    not just exact title matches. Need to search through many results.
    """
    base_url = "https://dblp.org/search/publ/api"
    
    # Use quotes for exact phrase matching (but still returns partial matches)
    query = f'"{title}"'
    
    params = {
        'q': query,
        'format': 'json',
        'h': max_results  
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(e)
        return None


def normalize_title(title):
    """Normalize title for comparison"""
    # Remove special characters, convert to lowercase
    import re
    normalized = re.sub(r'[^a-z0-9\s]', '', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def title_similarity(title1, title2):
    """Calculate similarity between two titles (0-1)"""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    return SequenceMatcher(None, norm1, norm2).ratio()

def extract_author_info(paper_data):
    """Extract author names and IDs from DBLP paper data"""
    authors = []
    
    # DBLP API returns author info in 'authors' field
    if 'authors' in paper_data and paper_data['authors']:
        author_list = paper_data['authors'].get('author', [])
        
        # Handle single author case (not a list)
        if isinstance(author_list, dict):
            author_list = [author_list]
        
        for author in author_list:
            if isinstance(author, dict):
                # DBLP uses '@pid' attribute, not 'pid'
                author_info = {
                    'name': author.get('text', ''),
                    'pid': author.get('@pid', author.get('pid', ''))  # Try both @pid and pid
                }
                authors.append(author_info)
            elif isinstance(author, str):
                # Sometimes it's just a string
                authors.append({'name': author, 'pid': ''})
    
    return authors

def find_exact_match(query_title, hit_list):
    """Find exact title match from search results
    
    Only returns 100% exact match (after normalization).
    No fuzzy matching - must be perfect match.
    
    Args:
        query_title: The title we're searching for
        hit_list: List of search results from DBLP
    
    Returns:
        (best_match, 1.0, 'exact') or (None, 0, None)
    """
    if not hit_list:
        return None, 0, None
    
    if not isinstance(hit_list, list):
        hit_list = [hit_list]
    
    query_norm = normalize_title(query_title)
    
    # Only find 100% exact match
    for hit in hit_list:
        paper_info = hit.get('info', {})
        result_title = paper_info.get('title', '')
        result_norm = normalize_title(result_title)
        
        if result_norm == query_norm:
            return hit
    
    # No exact match found
    return None

def smart_delay(base_delay=1):
    """Smart delay to be respectful to DBLP servers"""
    # DBLP API is more permissive, but still add delays
    delay = base_delay * random.uniform(0.8, 1.2)
    
    # Occasional longer delay
    if random.random() < 0.05:
        delay += random.uniform(2, 5)
    
    return delay


def process_single_paper(title):
    """Process a single paper: search DBLP and extract author info
    
    Returns:
        dict: Paper result with authors, dblp_key, and metadata
              Returns a dict with 'found': False if not found
    """
    # Search DBLP with exact phrase matching
    data = search_dblp(title, max_results=1000)
    
    if not data or 'result' not in data:
        return []
    
    hits = data['result'].get('hits', {})
    hit_list = hits.get('hit', [])
    total_hits = data['result']['hits'].get('@total', 0)
    
    if not hit_list:
        return []
    
    # Find exact title match
    best_match = find_exact_match(title, hit_list)
    
    if not best_match:
        return []
    
    # Extract authors
    paper_info = best_match.get('info', {})
    return extract_author_info(paper_info)




def main():


    print("  ")
    print(" - - - - - - - - - - Loading paper titles - - - - - - - - - - -")
    with open('/sensei-fs/users/yuhli/proj_citation/citation/cvpr_titles.json', 'r', encoding='utf-8') as f:
        titles = json.load(f)
    print(f"Total: {len(titles)} papers")



    print("  ")
    print(" - - - - - - - - - - Auto resume - - - - - - - - - - -")
    results = {}
    all_author_pids = set()
    
    try:
        with open('dblp_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        with open('all_dblp_author_pids.txt', 'r', encoding='utf-8') as f:
            all_author_pids = set(line.strip() for line in f if line.strip())
        print(f"✓ Found existing progress: {len(results)} processed, {len(all_author_pids)} unique author PIDs")
    except FileNotFoundError:
        print("No existing progress found, starting from scratch")
    
    # Process papers that haven't been processed OR had empty results (not found)
    remaining_titles = [t for t in titles if t not in results or not results[t]]
    
    # Count how many are retries (previously empty)
    retry_count = sum(1 for t in titles if t in results and not results[t])
    new_count = len(remaining_titles) - retry_count
    
    print(f"Remaining to process: {len(remaining_titles)} papers")
    print(f"  - New papers: {new_count}")
    print(f"  - Retry (previously empty): {retry_count}\n")
    
    if not remaining_titles:
        print("All papers have been processed! Exit...")
        return
    

    print("  ")
    print(" - - - - - - - - - - Running - - - - - - - - - - -")
    try:
        initial_count = len(results)  # Save initial count before loop
        for i, title in enumerate(remaining_titles):
            total_processed = initial_count + i + 1
            print(f"\n[{total_processed}/{len(titles)}] Processing: {title[:60]}...")
            
            try:
                # Process single paper - returns author list or empty list
                authors = process_single_paper(title)
                results[title] = authors
                
                # Collect author PIDs if found
                if authors:
                    for author in authors:
                        if author.get('pid'):
                            all_author_pids.add(author['pid'])

                # Save progress every 50 papers
                if (i + 1) % 50 == 0:
                    save_progress(results, all_author_pids)
                
                # Respectful delay
                delay = 0.5 if not authors else 1
                time.sleep(smart_delay(base_delay=delay))
                
            except Exception as e:
                results[title] = []
                time.sleep(2)
                continue
        
        # Final save
        save_progress(results, all_author_pids)
        print("Done.")

        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress...")
        save_progress(results, all_author_pids)
        print("Progress saved. You can resume later.")

def save_progress(results, all_pids):
    """Save progress to files"""
    # Save detailed results (paper -> authors mapping)
    with open('dblp_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save all unique author PIDs
    with open('all_dblp_author_pids.txt', 'w', encoding='utf-8') as f:
        for pid in sorted(all_pids):
            f.write(pid + '\n')
    
    print(f"\n💾 Progress saved: {len(results)} papers, {len(all_pids)} unique PIDs")

if __name__ == '__main__':
    main()

