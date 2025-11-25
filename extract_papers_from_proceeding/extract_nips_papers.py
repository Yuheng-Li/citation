#!/usr/bin/env python3
"""Extract papers from NeurIPS (papers.nips.cc)"""

import requests
from bs4 import BeautifulSoup
import json
import os

def extract_nips_papers(year: int):
    """
    Extract NeurIPS papers from papers.nips.cc
    
    Args:
        year: Year (e.g., 2025, 2024, 2023)
    
    Returns:
        List of paper dictionaries
    """
    url = f"https://papers.nips.cc/paper_files/paper/{year}"
    print(f"Extracting NeurIPS {year}...", end=' ', flush=True)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        papers = []
        
        # Find all li elements with class="conference"
        paper_lis = soup.find_all('li', class_='conference')
        
        for li in paper_lis:
            try:
                # Get title from <a> tag
                title_link = li.find('a')
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                href = title_link.get('href', '')
                paper_url = href
                if paper_url and not paper_url.startswith('http'):
                    paper_url = f"https://papers.nips.cc{paper_url}"
                
                # Get authors from <i> tag
                authors_tag = li.find('i')
                authors = []
                
                if authors_tag:
                    author_text = authors_tag.get_text(strip=True)
                    # Split by comma
                    if ',' in author_text:
                        authors = [a.strip() for a in author_text.split(',') if a.strip()]
                    else:
                        authors = [author_text] if author_text else []
                
                paper_info = {
                    'title': title,
                    'authors': authors,
                    'venue': f'NeurIPS {year}',
                    'year': year,
                    'url': paper_url,
                    'pdf_url': ''
                }
                
                papers.append(paper_info)
                
            except Exception:
                continue
        
        return papers
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def main():
    """Extract NeurIPS papers"""
    
    # Create output directory
    output_dir = 'conference_papers'
    os.makedirs(output_dir, exist_ok=True)
    
    # NeurIPS years (annual conference)
    years = [2024, 2023]
    
    for year in years:
        papers = extract_nips_papers(year)
        
        if papers:
            output_file = os.path.join(output_dir, f"nips_{year}_papers.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
            print(f"✓ {len(papers)} papers → {output_file}")
        else:
            print(f"⚠️ No papers found")


if __name__ == '__main__':
    main()

