#!/usr/bin/env python3
"""Extract papers from DBLP by conference and year"""

import requests
import json
import time

def extract_conference_papers(conference: str, year: int, output_file: str):
    """Extract papers from DBLP for a specific conference and year"""
    print(f"Extracting {conference} {year}...")
    
    papers = []
    hits_per_request = 500
    first_hit = 0
    max_retries = 3
    total_expected = None
    failed_due_to_error = False
    
    # Map conference abbreviations to DBLP stream keys
    conf_stream_map = {
        'CVPR': 'conf/cvpr',
        'ICCV': 'conf/iccv', 
        'ECCV': 'conf/eccv',
        'ICML': 'conf/icml',
        'ICLR': 'conf/iclr',
        'NIPS': 'conf/nips',
        'ACL': 'conf/acl',
        'EMNLP': 'conf/emnlp',
        'NAACL': 'conf/naacl'
    }
    
    stream_key = conf_stream_map.get(conference.upper())
    if not stream_key:
        print(f"Unknown conference: {conference}")
        return
    
    while True:
        # DBLP API endpoint
        url = "https://dblp.org/search/publ/api"
        params = {
            'q': f'streamid:{stream_key}* year:{year}',
            'format': 'json',
            'h': hits_per_request,
            'f': first_hit
        }
        
        # Retry mechanism
        data = None
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"Error: {e}")
                    break
        
        if data is None:
            failed_due_to_error = True
            break
        
        if 'result' not in data or 'hits' not in data['result']:
            break
        
        hits = data['result']['hits']
        total = int(data['result']['hits'].get('@total', 0))
        
        if total_expected is None:
            total_expected = total
            print(f"Total: {total} papers")
        
        if '@sent' not in hits or int(hits['@sent']) == 0:
            break
        
        hit_list = hits.get('hit', [])
        if not hit_list:
            break
        
        for hit in hit_list:
            info = hit.get('info', {})
            
            title = info.get('title', 'N/A')
            if isinstance(title, dict):
                title = title.get('#text', 'N/A')
            
            authors_data = info.get('authors', {}).get('author', [])
            if not isinstance(authors_data, list):
                authors_data = [authors_data]
            
            authors = []
            for author in authors_data:
                if isinstance(author, dict):
                    author_name = author.get('#text', author.get('text', ''))
                else:
                    author_name = str(author)
                if author_name:
                    authors.append(author_name)
            
            papers.append({
                'title': title,
                'authors': authors,
                'venue': info.get('venue', 'N/A'),
                'year': info.get('year', 'N/A'),
                'doi': info.get('doi', ''),
                'url': info.get('url', '')
            })
        
        # Check if we've got all results
        first_hit += len(hit_list)
        if first_hit >= total:
            break
        
        time.sleep(1.5)
    
    # Check if download was complete
    if failed_due_to_error or (total_expected and len(papers) < total_expected):
        print(f"ERROR: Incomplete download - {len(papers)}/{total_expected} papers")
        print(f"Reason: DBLP timeout/rate limiting. Try again later.")
        return
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(papers)} papers to {output_file}")


def main():
    conferences = ['cvpr', 'iccv', 'eccv', 'icml', 'iclr', 'nips', 'acl', 'emnlp', 'naacl']
    years = [2025, 2024, 2023]
    
    for conf in conferences:
        for year in years:
            output_file = f'{conf}_{year}_papers.json'
            extract_conference_papers(conf.upper(), year, output_file)
            time.sleep(10)  # Pause between conferences to avoid rate limiting


if __name__ == '__main__':
    main()

