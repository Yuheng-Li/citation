#!/usr/bin/env python3
"""Extract papers from ACL Anthology (aclanthology.org)"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from typing import List, Dict

def extract_acl_papers(conference: str, year: int, track: str = 'long') -> List[Dict]:
    """
    Extract papers from ACL Anthology (only specific track)
    
    Args:
        conference: Conference name (e.g., 'acl', 'naacl', 'emnlp')
        year: Year (e.g., 2025, 2024, 2023)
        track: Track name (e.g., 'long', 'main')
    
    Returns:
        List of paper dictionaries with title, authors, and pdf_url
    """
    # Construct URL based on conference
    if conference.lower() == 'emnlp':
        url = f"https://aclanthology.org/events/{conference.lower()}-{year}/#{year}{conference.lower()}-main"
        track_identifier = f"{year}.{conference.lower()}-main."
    else:  # acl, naacl
        url = f"https://aclanthology.org/events/{conference.lower()}-{year}/#{year}{conference.lower()}-long"
        track_identifier = f"{year}.{conference.lower()}-long."
    
    print(f"Extracting {conference.upper()} {year} ({track})...", end=' ', flush=True)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        papers = []
        
        # Find all paper entries with class 'paper'
        paper_entries = soup.find_all('p', class_='d-sm-flex align-items-stretch')
        
        for paper in paper_entries:
            try:
                # Extract title
                title_link = paper.find('strong').find('a') if paper.find('strong') else None
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                paper_url = title_link.get('href', '')
                if paper_url and not paper_url.startswith('http'):
                    paper_url = f"https://aclanthology.org{paper_url}"
                
                # FILTER: Only include papers from the specific track
                # Check if the URL contains the track identifier
                if track_identifier not in paper_url:
                    continue
                
                # Extract authors
                authors = []
                author_spans = paper.find_all('a', href=lambda x: x and '/people/' in x)
                for author_link in author_spans:
                    author_name = author_link.get_text(strip=True)
                    if author_name:
                        authors.append(author_name)
                
                # Get PDF URL
                pdf_link = paper.find('a', class_='badge badge-primary align-middle mr-1', href=lambda x: x and '.pdf' in x)
                pdf_url = ''
                if pdf_link:
                    pdf_url = pdf_link.get('href', '')
                    if pdf_url and not pdf_url.startswith('http'):
                        pdf_url = f"https://aclanthology.org{pdf_url}"
                
                paper_info = {
                    'title': title,
                    'authors': authors,
                    'venue': f"{conference.upper()} {year}",
                    'year': year,
                    'url': paper_url,
                    'pdf_url': pdf_url
                }
                
                papers.append(paper_info)
                
            except Exception:
                continue
        
        return papers
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []


def main():
    """Extract papers from NLP conferences"""
    
    # Create output directory
    output_dir = 'conference_papers'
    os.makedirs(output_dir, exist_ok=True)
    
    # Configuration
    conferences = [
        ('naacl', [2025, 2024]),
        ('acl', [2025, 2024, 2023]),
        ('emnlp', [2025, 2024, 2023]),
    ]
    
    for conf_name, years in conferences:
        for year in years:
            output_file = os.path.join(output_dir, f"{conf_name.lower()}_{year}_papers.json")
            
            papers = extract_acl_papers(conf_name, year)
            
            if papers:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(papers, f, indent=2, ensure_ascii=False)
                print(f"✓ {len(papers)} papers → {output_file}")
            else:
                print(f"⚠️ No papers found")
            
            time.sleep(3)


if __name__ == '__main__':
    main()

