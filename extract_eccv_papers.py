#!/usr/bin/env python3
"""Extract papers from ECCV (www.ecva.net/papers.php)"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re

def extract_eccv_papers(year: int = 2024):
    """
    Extract ECCV papers from www.ecva.net/papers.php
    
    Args:
        year: Year (e.g., 2024, 2022, 2020)
    
    Returns:
        List of paper dictionaries
    """
    url = "https://www.ecva.net/papers.php"
    print(f"Extracting ECCV {year}...", end=' ', flush=True)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        papers = []
        
        # Find all dt elements (paper titles)
        all_dt = soup.find_all('dt')
        
        for dt in all_dt:
            try:
                # Get the title link
                title_link = dt.find('a')
                if not title_link:
                    continue
                
                # Filter by year in the URL
                href = title_link.get('href', '')
                if f'eccv_{year}' not in href.lower():
                    continue
                
                title = title_link.get_text(strip=True)
                paper_url = href
                if paper_url and not paper_url.startswith('http'):
                    paper_url = f"https://www.ecva.net/{paper_url}"
                
                # Get authors from next dd element
                dd = dt.find_next_sibling('dd')
                authors = []
                
                if dd:
                    # Authors are separated by commas
                    # Remove asterisks (marking corresponding authors)
                    author_text = dd.get_text(strip=True)
                    author_text = author_text.replace('*', '')
                    
                    # Split by comma
                    if ',' in author_text:
                        authors = [a.strip() for a in author_text.split(',') if a.strip()]
                    else:
                        authors = [author_text] if author_text else []
                
                paper_info = {
                    'title': title,
                    'authors': authors,
                    'venue': f'ECCV {year}',
                    'year': year,
                    'url': paper_url,
                    'pdf_url': ''  # ECCV site structure is different
                }
                
                papers.append(paper_info)
                
            except Exception:
                continue
        
        return papers
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def main():
    """Extract ECCV papers"""
    
    # Create output directory
    output_dir = 'conference_papers'
    os.makedirs(output_dir, exist_ok=True)
    
    # ECCV years (biennial, even years)
    years = [2024]
    
    for year in years:
        papers = extract_eccv_papers(year)
        
        if papers:
            output_file = os.path.join(output_dir, f"eccv_{year}_papers.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
            print(f"✓ {len(papers)} papers → {output_file}")
        else:
            print(f"⚠️ No papers found for ECCV {year}")


if __name__ == '__main__':
    main()

