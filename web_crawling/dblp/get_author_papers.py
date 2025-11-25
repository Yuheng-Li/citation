"""
Get all papers from a DBLP author by PID
"""

import requests
import json
import time

def get_author_papers(pid):
    """Get all papers from DBLP author by PID
    
    Args:
        pid: DBLP author PID (e.g., '34/7659' for Kaiming He)
    
    Returns:
        dict with author info and papers list
    """
    # DBLP author API endpoint
    base_url = f"https://dblp.org/pid/{pid}.xml"
    
    print(f"\nFetching papers for author PID: {pid}")
    print(f"URL: {base_url}")
    
    try:
        # Request XML format (DBLP doesn't provide JSON for author pages)
        response = requests.get(base_url, timeout=15)
        response.raise_for_status()
        
        # Parse XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        # Get author name
        author_name = root.findtext('.//author', default='Unknown')
        
        # Get all publications
        papers = []
        
        for pub in root.findall('.//r'):
            # Each publication can be article, inproceedings, etc.
            pub_elem = pub.find('*')  # Get first child (the actual publication)
            
            if pub_elem is None:
                continue
            
            pub_type = pub_elem.tag
            
            # Extract paper info
            paper = {
                'type': pub_type,
                'title': pub_elem.findtext('title', default=''),
                'year': pub_elem.findtext('year', default=''),
                'venue': pub_elem.findtext('booktitle', default=pub_elem.findtext('journal', default='')),
                'key': pub_elem.get('key', ''),
                'authors': []
            }
            
            # Get all authors
            for author in pub_elem.findall('author'):
                author_info = {
                    'name': author.text,
                    'pid': author.get('pid', '')
                }
                paper['authors'].append(author_info)
            
            papers.append(paper)
        
        result = {
            'author_name': author_name,
            'author_pid': pid,
            'total_papers': len(papers),
            'papers': papers
        }
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def save_author_papers(pid, output_file=None):
    """Fetch and save author papers to JSON file"""
    
    data = get_author_papers(pid)
    
    if not data:
        print("Failed to fetch data")
        return
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"Author: {data['author_name']}")
    print(f"PID: {data['author_pid']}")
    print(f"Total Papers: {data['total_papers']}")
    print('='*70)
    
    # Show paper stats by type
    type_counts = {}
    year_counts = {}
    
    for paper in data['papers']:
        pub_type = paper['type']
        year = paper['year']
        
        type_counts[pub_type] = type_counts.get(pub_type, 0) + 1
        year_counts[year] = year_counts.get(year, 0) + 1
    
    print(f"\n📊 Publication Types:")
    for pub_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pub_type}: {count}")
    
    print(f"\n📅 Recent Years:")
    for year, count in sorted(year_counts.items(), reverse=True)[:10]:
        print(f"  {year}: {count}")
    
    # Show sample papers
    print(f"\n📄 Sample Papers (first 5):")
    for i, paper in enumerate(data['papers'][:5], 1):
        print(f"\n  {i}. {paper['title']}")
        print(f"     {paper['venue']} {paper['year']}")
        print(f"     Authors: {len(paper['authors'])}")
    
    # Save to file
    if output_file is None:
        # Generate filename from author name
        author_slug = data['author_name'].lower().replace(' ', '_')
        output_file = f"author_{author_slug}_{pid.replace('/', '_')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {output_file}")
    print('='*70 + '\n')

def main():
    # Example: Kaiming He
    kaiming_pid = "34/7659"
    
    save_author_papers(kaiming_pid)

if __name__ == '__main__':
    main()

