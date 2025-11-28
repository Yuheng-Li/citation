import requests
import xml.etree.ElementTree as ET
import time

def search_arxiv_by_title(title):
    """Search arXiv by paper title and get detailed information"""
    base_url = "http://export.arxiv.org/api/query"
    
    # Search query - exact title match
    query = f'ti:"{title}"'
    params = {
        "search_query": query,
        "max_results": 5  # Get top 5 results
    }
    
    print(f"Searching arXiv for: {title}\n")
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Namespace
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        # Find all entries
        entries = root.findall('atom:entry', ns)
        
        if not entries:
            print("No results found on arXiv")
            return None
        
        results = []
        for i, entry in enumerate(entries, 1):
            result = {}
            
            # Title
            title_elem = entry.find('atom:title', ns)
            if title_elem is not None:
                result['title'] = title_elem.text.strip().replace('\n', ' ')
            
            # arXiv ID
            id_elem = entry.find('atom:id', ns)
            if id_elem is not None:
                result['arxiv_id'] = id_elem.text.split('/')[-1]
            
            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    authors.append(name.text)
            result['authors'] = authors
            
            # Abstract
            summary = entry.find('atom:summary', ns)
            if summary is not None:
                result['abstract'] = summary.text.strip().replace('\n', ' ')[:200] + "..."
            
            # Published date
            published = entry.find('atom:published', ns)
            if published is not None:
                result['published'] = published.text.split('T')[0]
            
            # PDF link
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    result['pdf_url'] = link.get('href')
            
            # Categories
            categories = []
            for category in entry.findall('atom:category', ns):
                categories.append(category.get('term'))
            result['categories'] = categories
            
            results.append(result)
            
            # Print result
            print(f"Result {i}:")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  arXiv ID: {result.get('arxiv_id', 'N/A')}")
            print(f"  Authors: {', '.join(result.get('authors', [])[:3])}{'...' if len(result.get('authors', [])) > 3 else ''}")
            print(f"  Published: {result.get('published', 'N/A')}")
            print(f"  Categories: {', '.join(result.get('categories', []))}")
            print(f"  PDF URL: {result.get('pdf_url', 'N/A')}")
            print(f"  Abstract: {result.get('abstract', 'N/A')}")
            print()
        
        return results
    else:
        print(f"Error: HTTP {response.status_code}")
        return None


# Demo: Search for the paper
if __name__ == "__main__":
    paper_title = "Removing Distributional Discrepancies in Captions Improves Image-Text Alignment"
    
    results = search_arxiv_by_title(paper_title)
    
    if results:
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Found {len(results)} results on arXiv")
        
        if results[0]:
            print(f"\nBest match:")
            print(f"  PDF: {results[0].get('pdf_url', 'N/A')}")
            print(f"  arXiv ID: {results[0].get('arxiv_id', 'N/A')}")
    else:
        print("No results found")

