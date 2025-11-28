#!/usr/bin/env python3
"""
SerpAPI Google Scholar Author - Get all papers with pagination support
"""

import json
import time
from serpapi import GoogleSearch


def get_all_author_articles(author_id, api_key, delay=3, max_pages=5, sort_by_date=True):
    """
    Get all papers for an author with automatic pagination
    
    Args:
        author_id: Google Scholar author ID
        api_key: SerpAPI API key
        delay: Delay between requests in seconds to avoid rate limiting
        max_pages: Maximum number of pages to request (default 5 pages = max 500 papers)
        sort_by_date: Sort by publication date (newest first), default True
    
    Returns:
        dict: Complete author information including all papers
    """
    params = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "api_key": api_key,
        "hl": "en",
        "num": 100,
        "start": 0
    }
    
    if sort_by_date:
        params["sort"] = "pubdate"  # Sort by publication date (newest first)
    
    search = GoogleSearch(params)
    results = search.get_dict()
    all_articles = results.get('articles', [])
    
    page = 2
    while 'serpapi_pagination' in results and 'next' in results['serpapi_pagination']:
        if page > max_pages:
            break
        
        time.sleep(delay)
        
        params['start'] = (page - 1) * 100
        search = GoogleSearch(params)
        next_results = search.get_dict()
        
        next_articles = next_results.get('articles', [])
        if not next_articles:
            break
            
        all_articles.extend(next_articles)
        results = next_results
        page += 1
    
    results['articles'] = all_articles
    
    if page > max_pages and 'serpapi_pagination' in results and 'next' in results['serpapi_pagination']:
        results['_note'] = f"Author may have more papers."
    else:
        results['_note'] = "All papers retrieved."
    
    return results


def main():
    """Main function"""
    API_KEY = "4208bf0e57fee689890d366d525744e54cf91c1c7dd3606506c8c42ca5dbea41"
    author_id = "3TMipekAAAAJ"
    
    # Get articles sorted by date (newest first), up to 500 papers (5 pages)
    results = get_all_author_articles(
        author_id, 
        API_KEY, 
        delay=1, 
        max_pages=5, 
        sort_by_date=True  # Sort by publication date (2025 -> older)
    )
    
    output_file = f"author_{author_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

