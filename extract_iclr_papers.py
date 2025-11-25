#!/usr/bin/env python3
"""Extract accepted papers from ICLR via OpenReview API"""

import requests
import json
import os
import time

def extract_iclr_papers(year: int):
    """
    Extract ICLR accepted papers from OpenReview API
    
    Args:
        year: Year (e.g., 2025, 2024, 2023)
    
    Returns:
        List of paper dictionaries
    """
    print(f"Extracting ICLR {year}...", end=' ', flush=True)
    
    api_url = "https://api2.openreview.net/notes"
    papers = []
    offset = 0
    limit = 1000  # Fetch in batches
    
    try:
        while True:
            params = {
                'invitation': f'ICLR.cc/{year}/Conference/-/Submission',
                'details': 'replies',
                'limit': limit,
                'offset': offset
            }
            
            response = requests.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            notes = data.get('notes', [])
            
            if not notes:
                break
            
            for note in notes:
                try:
                    content = note.get('content', {})
                    
                    # Extract title
                    title_data = content.get('title', {})
                    title = title_data.get('value', '') if isinstance(title_data, dict) else str(title_data)
                    
                    # Extract authors
                    authors_data = content.get('authors', {})
                    if isinstance(authors_data, dict):
                        authors = authors_data.get('value', [])
                    else:
                        authors = authors_data if isinstance(authors_data, list) else []
                    
                    # Check if accepted (venue field indicates acceptance)
                    venue_data = content.get('venue', {})
                    venue = venue_data.get('value', '') if isinstance(venue_data, dict) else str(venue_data)
                    
                    # Only include accepted papers (Oral, Spotlight, or Poster)
                    # Exclude: Submitted, Withdrawn, Rejected, Desk Rejected
                    accepted = False
                    if venue:
                        venue_str = str(venue)
                        venue_lower = venue_str.lower()
                        if (('oral' in venue_lower or 'spotlight' in venue_lower or 'poster' in venue_lower) 
                            and str(year) in venue_str
                            and 'withdrawn' not in venue_lower 
                            and 'reject' not in venue_lower
                            and 'submitted' not in venue_lower):
                            accepted = True
                    
                    if accepted:
                        # Get paper URL
                        paper_id = note.get('id', '')
                        paper_url = f"https://openreview.net/forum?id={paper_id}" if paper_id else ''
                        
                        # Get PDF URL if available
                        pdf_data = content.get('pdf', {})
                        pdf_url = pdf_data.get('value', '') if isinstance(pdf_data, dict) else str(pdf_data)
                        if pdf_url and not pdf_url.startswith('http'):
                            pdf_url = f"https://openreview.net{pdf_url}" if pdf_url else ''
                        
                        paper_info = {
                            'title': title,
                            'authors': authors,
                            'venue': f'ICLR {year}',
                            'year': year,
                            'url': paper_url,
                            'pdf_url': pdf_url
                        }
                        
                        papers.append(paper_info)
                
                except Exception:
                    continue
            
            offset += len(notes)
            
            # If we got fewer results than limit, we've reached the end
            if len(notes) < limit:
                break
            
            time.sleep(0.5)  # Be nice to the API
        
        return papers
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def main():
    """Extract ICLR papers"""
    
    # Create output directory
    output_dir = 'conference_papers'
    os.makedirs(output_dir, exist_ok=True)
    
    # ICLR years (annual conference)
    years = [2025, 2024, 2023]
    
    for year in years:
        papers = extract_iclr_papers(year)
        
        if papers:
            output_file = os.path.join(output_dir, f"iclr_{year}_papers.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
            print(f"✓ {len(papers)} papers → {output_file}")
        else:
            print(f"⚠️ No papers found")
        
        time.sleep(1)  # Pause between years


if __name__ == '__main__':
    main()

