#!/usr/bin/env python3
"""Extract papers from CVF Open Access (openaccess.thecvf.com)"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from typing import List, Dict

def extract_cvf_papers(conference: str, year: int) -> List[Dict]:
    """
    Extract papers from CVF Open Access
    
    Args:
        conference: Conference name (e.g., 'CVPR', 'ICCV', 'WACV')
        year: Year (e.g., 2025, 2024, 2023)
    
    Returns:
        List of paper dictionaries with title, authors, and pdf_url
    """
    url = f"https://openaccess.thecvf.com/{conference}{year}?day=all"
    print(f"Extracting {conference} {year}...", end=' ', flush=True)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        papers = []
        
        # Find all paper entries
        paper_titles = soup.find_all('dt', class_='ptitle')
        if not paper_titles:
            paper_titles = soup.find_all('dt')
        
        for dt in paper_titles:
            try:
                # Extract title
                title_link = dt.find('a')
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                paper_url = title_link.get('href', '')
                if paper_url and not paper_url.startswith('http'):
                    paper_url = f"https://openaccess.thecvf.com{paper_url}"
                
                # Extract authors (usually in the next dd tag)
                dd = dt.find_next_sibling('dd')
                authors = []
                pdf_url = ''
                
                if dd:
                    # Authors are in form elements with hidden inputs
                    author_forms = dd.find_all('form', class_='authsearch')
                    for form in author_forms:
                        author_input = form.find('input', {'name': 'query_author'})
                        if author_input:
                            author_name = author_input.get('value', '').strip()
                            if author_name:
                                authors.append(author_name)
                    
                    # Try to find PDF link
                    pdf_link = dd.find('a', string=lambda t: t and 'pdf' in t.lower())
                    if pdf_link:
                        pdf_url = pdf_link.get('href', '')
                        if pdf_url and not pdf_url.startswith('http'):
                            pdf_url = f"https://openaccess.thecvf.com{pdf_url}"
                
                paper_info = {
                    'title': title,
                    'authors': authors,
                    'venue': f"{conference} {year}",
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
    """Extract papers from multiple conferences and years"""
    
    # Create output directory
    output_dir = 'conference_papers'
    os.makedirs(output_dir, exist_ok=True)
    
    # Configuration
    conferences = [
        ('CVPR', [2025, 2024, 2023]),
        ('ICCV', [2025, 2023]),  # ICCV is biennial (odd years)
    ]
    
    for conf_name, years in conferences:
        for year in years:
            output_file = os.path.join(output_dir, f"{conf_name.lower()}_{year}_papers.json")
            
            papers = extract_cvf_papers(conf_name, year)
            
            if papers:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(papers, f, indent=2, ensure_ascii=False)
                print(f"✓ {len(papers)} papers → {output_file}")
            else:
                print(f"⚠️ No papers found")
            
            time.sleep(3)


if __name__ == '__main__':
    main()

