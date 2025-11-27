import requests
import re
import json
import time
from urllib.parse import quote_plus

# Bright Data configuration
headers = {
    "Authorization": "Bearer 95f1e5b4c7ef79702fb77666561a234104bba6d008706c56d95f27dcae3daa9a",
    "Content-Type": "application/json"
}

# Load paper data
json_file = "/sensei-fs/users/yuhli/proj_citation/citation/activate_authors_and_paper/v1/minimal_paper_set.json"
with open(json_file, 'r', encoding='utf-8') as f:
    papers = json.load(f)
print(f"Loaded {len(papers)} papers, starting search...\n")

# Output file path
output_file = "/sensei-fs/users/yuhli/proj_citation/citation/web_crawling/search_results.json"

# Try to load existing results (support resume)
all_results = []
processed_titles = set()

try:
    with open(output_file, 'r', encoding='utf-8') as f:
        all_results = json.load(f)
        processed_titles = {r['title'] for r in all_results}
        print(f"Found existing results, already processed {len(processed_titles)} papers, resuming...\n")
except FileNotFoundError:
    print("No existing results found, starting from scratch...\n")

# Process papers one by one
save_interval = 10
processed_count = 0

for idx, paper in enumerate(papers, 1):
    title = paper.get("title", "")
    
    # Skip already processed papers
    if title in processed_titles:
        continue
    
    authors = paper.get("authors", [])
    
    if not title:
        continue
    
    # Build search query: title + first 5 authors
    query_parts = [title]
    top_authors = authors[:5] if len(authors) > 5 else authors
    query_parts.extend(top_authors)
    
    search_query = " ".join(query_parts)
    encoded_query = quote_plus(search_query)
    
    # Build Google Scholar search URL
    scholar_url = f"https://scholar.google.com/scholar?q={encoded_query}"
    
    data = {
        "zone": "yuheng_serp",
        "url": scholar_url,
        "format": "raw"
    }
    
    print(f"Progress: [{idx}/{len(papers)}] (Processed: {len(all_results)})")
    
    try:
        response = requests.post(
            "https://api.brightdata.com/request",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            html = response.text
            
            # Extract Google Scholar IDs
            pattern = r'/citations\?user=([^&"\']+)'
            scholar_ids = list(set(re.findall(pattern, html)))
            
            all_results.append({
                "title": title,
                "authors": authors,
                "scholar_ids": scholar_ids,
                "scholar_url": scholar_url
            })
        else:
            all_results.append({
                "title": title,
                "authors": authors,
                "scholar_ids": [],
                "scholar_url": scholar_url
            })
    
    except Exception as e:
        all_results.append({
            "title": title,
            "authors": authors,
            "scholar_ids": [],
            "scholar_url": scholar_url
        })
    
    processed_count += 1
    
    # Save every N papers
    if processed_count % save_interval == 0:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # Add delay to avoid rate limiting
    time.sleep(0.5)

# Final save (ensure all results are saved)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"\nSearch completed!")
print(f"Total processed: {len(all_results)} | Found scholar IDs: {sum(1 for r in all_results if r['scholar_ids'])}")
print(f"Results saved to: {output_file}")

# Extract all unique scholar IDs
unique_scholar_ids = set()
for result in all_results:
    scholar_ids = result.get('scholar_ids', [])
    unique_scholar_ids.update(scholar_ids)

unique_scholar_ids = sorted(list(unique_scholar_ids))

# Save unique scholar IDs
unique_ids_file = "/sensei-fs/users/yuhli/proj_citation/citation/web_crawling/unique_scholar_ids.json"
with open(unique_ids_file, 'w', encoding='utf-8') as f:
    json.dump(unique_scholar_ids, f, ensure_ascii=False, indent=2)

print(f"\nUnique scholar IDs: {len(unique_scholar_ids)}")
print(f"Saved to: {unique_ids_file}")
