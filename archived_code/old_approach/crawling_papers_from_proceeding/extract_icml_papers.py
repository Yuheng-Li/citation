#!/usr/bin/env python3
"""Extract papers from ICML via PMLR (proceedings.mlr.press)"""

import requests
from bs4 import BeautifulSoup
import json
import os

def extract_icml_papers(year: int, volume: int):
    """
    Extract ICML papers from PMLR
    
    Args:
        year: Year (e.g., 2025, 2024, 2023)
        volume: PMLR volume number (e.g., 267 for 2025, 235 for 2024, 202 for 2023)
    
    Returns:
        List of paper dictionaries
    """
    url = f"https://proceedings.mlr.press/v{volume}/"
    print(f"Extracting ICML {year}...", end=' ', flush=True)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        papers = []
        
        # Find all papers by looking for <p class="links">
        link_paragraphs = soup.find_all('p', class_='links')
        
        for links_p in link_paragraphs:
            try:
                # Get authors paragraph (previous sibling)
                authors_p = links_p.find_previous_sibling('p')
                if not authors_p:
                    continue
                
                authors_text = authors_p.get_text(strip=True)
                
                # Parse authors (before semicolon)
                authors = []
                if ';' in authors_text:
                    authors_str = authors_text.split(';')[0]
                    authors = [a.strip() for a in authors_str.split(',') if a.strip()]
                
                # Get title (element before authors paragraph)
                title_elem = authors_p.find_previous_sibling()
                title = ''
                if title_elem:
                    title = title_elem.get_text(strip=True)
                
                # Get paper URL
                abs_link = links_p.find('a', string='abs')
                paper_url = ''
                if abs_link:
                    paper_url = abs_link.get('href', '')
                    if paper_url and not paper_url.startswith('http'):
                        paper_url = f"https://proceedings.mlr.press{paper_url}"
                
                # Get PDF URL
                pdf_link = links_p.find('a', string='Download PDF')
                pdf_url = ''
                if pdf_link:
                    pdf_url = pdf_link.get('href', '')
                
                if title and authors:  # Only add if we have title and authors
                    paper_info = {
                        'title': title,
                        'authors': authors,
                        'venue': f'ICML {year}',
                        'year': year,
                        'url': paper_url,
                        'pdf_url': pdf_url
                    }
                    
                    papers.append(paper_info)
                
            except Exception:
                continue
        
        return papers
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def main():
    """Extract ICML papers"""
    
    # Create output directory
    output_dir = 'conference_papers'
    os.makedirs(output_dir, exist_ok=True)
    
    # ICML years and corresponding PMLR volumes
    conferences = [
        (2025, 267),  # ICML 2025 = v267
        (2024, 235),  # ICML 2024 = v235
        (2023, 202),  # ICML 2023 = v202
    ]
    
    for year, volume in conferences:
        papers = extract_icml_papers(year, volume)
        
        if papers:
            output_file = os.path.join(output_dir, f"icml_{year}_papers.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
            print(f"✓ {len(papers)} papers → {output_file}")
        else:
            print(f"⚠️ No papers found")


if __name__ == '__main__':
    main()



