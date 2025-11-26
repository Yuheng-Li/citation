import requests
import re
import json
from bs4 import BeautifulSoup

# Bright Data配置
headers = {
    "Authorization": "Bearer bb8030e2eec9cb8c59fe142d25d4dd4758c0f43946f547cd234760af4cbed3ce",
    "Content-Type": "application/json"
}

def parse_author_papers(html):
    """Parse all papers from a Google Scholar author profile page"""
    soup = BeautifulSoup(html, 'html.parser')
    papers = []
    
    # Find author name
    author_name_tag = soup.find('div', {'id': 'gsc_prf_in'})
    author_name = author_name_tag.text.strip() if author_name_tag else "Unknown"
    
    # Find all paper rows
    paper_rows = soup.find_all('tr', class_='gsc_a_tr')
    
    for row in paper_rows:
        try:
            paper = {}
            
            # Title and link
            title_tag = row.find('a', class_='gsc_a_at')
            if title_tag:
                paper['title'] = title_tag.text.strip()
                paper['url'] = 'https://scholar.google.com' + title_tag.get('href', '') if title_tag.get('href') else ''
            
            # Authors and publication info
            info_tag = row.find('div', class_='gs_gray')
            if info_tag:
                paper['authors'] = info_tag.text.strip()
            
            # Publication venue and year
            venue_tag = info_tag.find_next_sibling('div', class_='gs_gray') if info_tag else None
            if venue_tag:
                venue_text = venue_tag.text.strip()
                paper['venue'] = venue_text
                
                # Extract year from venue
                year_match = re.search(r'\b(19|20)\d{2}\b', venue_text)
                if year_match:
                    paper['year'] = int(year_match.group())
            
            # Citations
            citation_tag = row.find('a', class_='gsc_a_ac')
            if citation_tag and citation_tag.text.strip():
                try:
                    paper['citations'] = int(citation_tag.text.strip())
                except:
                    paper['citations'] = 0
            else:
                paper['citations'] = 0
            
            # Year (from separate column)
            year_tag = row.find('span', class_='gsc_a_h')
            if year_tag and year_tag.text.strip():
                try:
                    paper['year'] = int(year_tag.text.strip())
                except:
                    pass
            
            papers.append(paper)
            
        except Exception as e:
            print(f"  Error parsing paper: {e}")
            continue
    
    return {
        'author_name': author_name,
        'paper_count': len(papers),
        'papers': papers
    }


# Fetch author profile (top 20 papers only - Bright Data limitation)
scholar_id = "lc45xlcAAAAJ"  # Example: Ziwei Liu

def fetch_author_papers(scholar_id):
    """Fetch author's top 20 papers (most cited)"""
    scholar_url = f"https://scholar.google.com/citations?user={scholar_id}&hl=en&pagesize=100"
    
    print(f"Fetching author profile: {scholar_id}")
    print("Note: Only top 20 papers will be fetched (Bright Data limitation)\n")
    
    data = {
        "zone": "yuheng_serp",
        "url": scholar_url,
        "format": "raw"
    }
    
    response = requests.post(
        "https://api.brightdata.com/request",
        json=data,
        headers=headers
    )
    
    if response.status_code == 200:
        html = response.text
        
        if len(html) > 0:
            result = parse_author_papers(html)
            print(f"✓ Successfully fetched {result['paper_count']} papers")
            return result
        else:
            print("✗ Empty response")
            return None
    else:
        print(f"✗ Request failed: {response.status_code}")
        return None

# Fetch papers
result = fetch_author_papers(scholar_id)

if result and result['paper_count'] > 0:
    print("\n" + "="*80)
    print(f"Author: {result['author_name']}")
    print(f"Total papers found: {result['paper_count']}")
    print("="*80)
    
    # Show all papers (max 20)
    print("\nPapers:")
    for i, paper in enumerate(result['papers'], 1):
        print(f"\n{i}. {paper.get('title', 'N/A')}")
        print(f"   Authors: {paper.get('authors', 'N/A')[:100]}...")
        print(f"   Venue: {paper.get('venue', 'N/A')[:80]}")
        print(f"   Year: {paper.get('year', 'N/A')}")
        print(f"   Citations: {paper.get('citations', 0)}")
    
    # Save to JSON
    output_file = f'author_{scholar_id}_papers.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ All {result['paper_count']} papers saved to: {output_file}")
else:
    print("⚠️  No papers found")