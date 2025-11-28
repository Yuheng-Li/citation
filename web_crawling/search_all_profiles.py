import requests
import re
import json
import time
import os
from bs4 import BeautifulSoup
from multiprocessing import Pool
from functools import partial

# Bright Data configuration
headers = {
    "Authorization": "Bearer 95f1e5b4c7ef79702fb77666561a234104bba6d008706c56d95f27dcae3daa9a",
    "Content-Type": "application/json"
}

def parse_author_profile(html):
    """Parse complete author profile from Google Scholar page"""
    soup = BeautifulSoup(html, 'html.parser')
    
    profile = {
        "author_info": {},
        "citation_stats": {},
        "papers": [],
        "co_authors": []
    }
    
    # Author Basic Information
    author_name_tag = soup.find('div', {'id': 'gsc_prf_in'})
    if author_name_tag:
        profile["author_info"]["name"] = author_name_tag.text.strip()
    
    affiliation_tag = soup.find('div', class_='gsc_prf_il')
    if affiliation_tag:
        profile["author_info"]["affiliation"] = affiliation_tag.text.strip()
    
    email_tag = soup.find('div', {'id': 'gsc_prf_ivh'})
    if email_tag:
        profile["author_info"]["email_verified"] = email_tag.text.strip()
        website_link = email_tag.find('a')
        if website_link:
            profile["author_info"]["website"] = website_link.get('href', '')
    
    interests = []
    interest_tags = soup.find_all('a', class_='gsc_prf_inta')
    for tag in interest_tags:
        interests.append(tag.text.strip())
    profile["author_info"]["interests"] = interests
    
    photo_tag = soup.find('img', {'id': 'gsc_prf_pup-img'})
    if photo_tag:
        profile["author_info"]["photo_url"] = photo_tag.get('src', '')
    
    # Citation Statistics
    citation_table = soup.find('table', {'id': 'gsc_rsb_st'})
    if citation_table:
        rows = citation_table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) >= 3:
                stat_name = cells[0].text.strip()
                all_time = cells[1].text.strip()
                since_2020 = cells[2].text.strip()
                
                if stat_name == "Citations":
                    profile["citation_stats"]["citations_all"] = int(all_time) if all_time.isdigit() else 0
                    profile["citation_stats"]["citations_since_2020"] = int(since_2020) if since_2020.isdigit() else 0
                elif stat_name == "h-index":
                    profile["citation_stats"]["h_index_all"] = int(all_time) if all_time.isdigit() else 0
                    profile["citation_stats"]["h_index_since_2020"] = int(since_2020) if since_2020.isdigit() else 0
                elif stat_name == "i10-index":
                    profile["citation_stats"]["i10_index_all"] = int(all_time) if all_time.isdigit() else 0
                    profile["citation_stats"]["i10_index_since_2020"] = int(since_2020) if since_2020.isdigit() else 0
    
    citation_graph = []
    graph_bars = soup.find_all('span', class_='gsc_g_t')
    graph_values = soup.find_all('span', class_='gsc_g_al')
    for year_tag, value_tag in zip(graph_bars, graph_values):
        try:
            year = int(year_tag.text.strip())
            citations = int(value_tag.text.strip())
            citation_graph.append({"year": year, "citations": citations})
        except:
            pass
    profile["citation_stats"]["citation_graph"] = citation_graph
    
    # Papers
    paper_rows = soup.find_all('tr', class_='gsc_a_tr')
    for row in paper_rows:
        try:
            paper = {}
            
            title_tag = row.find('a', class_='gsc_a_at')
            if title_tag:
                paper['title'] = title_tag.text.strip()
                paper['url'] = 'https://scholar.google.com' + title_tag.get('href', '') if title_tag.get('href') else ''
            
            info_tag = row.find('div', class_='gs_gray')
            if info_tag:
                paper['authors'] = info_tag.text.strip()
            
            venue_tag = info_tag.find_next_sibling('div', class_='gs_gray') if info_tag else None
            if venue_tag:
                venue_text = venue_tag.text.strip()
                paper['venue'] = venue_text
                year_match = re.search(r'\b(19|20)\d{2}\b', venue_text)
                if year_match:
                    paper['year'] = int(year_match.group())
            
            citation_tag = row.find('a', class_='gsc_a_ac')
            if citation_tag and citation_tag.text.strip():
                try:
                    paper['citations'] = int(citation_tag.text.strip())
                except:
                    paper['citations'] = 0
            else:
                paper['citations'] = 0
            
            year_tag = row.find('span', class_='gsc_a_h')
            if year_tag and year_tag.text.strip():
                try:
                    paper['year'] = int(year_tag.text.strip())
                except:
                    pass
            
            profile["papers"].append(paper)
        except:
            continue
    
    # Co-authors
    coauthor_divs = soup.find_all('div', class_='gsc_rsb_aa')
    for div in coauthor_divs:
        try:
            coauthor = {}
            name_tag = div.find('a')
            if name_tag:
                coauthor['name'] = name_tag.text.strip()
                link = name_tag.get('href', '')
                if 'user=' in link:
                    author_id = link.split('user=')[1].split('&')[0]
                    coauthor['scholar_id'] = author_id
                    coauthor['url'] = f"https://scholar.google.com/citations?user={author_id}"
            
            affiliation_tag = div.find('div', class_='gsc_rsb_a_ext')
            if affiliation_tag:
                coauthor['affiliation'] = affiliation_tag.text.strip()
            
            if coauthor:
                profile["co_authors"].append(coauthor)
        except:
            continue
    
    # Sort papers by year (newest first)
    profile["papers"].sort(key=lambda p: p.get('year', 0), reverse=True)
    
    return profile


def fetch_author_profile(scholar_id):
    """Fetch complete author profile (top 20 papers - Bright Data limitation)"""
    scholar_url = f"https://scholar.google.com/citations?hl=en&user={scholar_id}"
    
    data = {
        "zone": "yuheng_serp",
        "url": scholar_url,
        "format": "raw"
    }
    
    try:
        response = requests.post(
            "https://api.brightdata.com/request",
            json=data,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200 and len(response.text) > 0:
            return parse_author_profile(response.text)
        return None
    except:
        return None


def process_single_author(scholar_id, output_dir):
    """Process a single author and save to file"""
    try:
        profile = fetch_author_profile(scholar_id)
        
        if profile:
            output_file = os.path.join(output_dir, f"author_{scholar_id}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            return (scholar_id, True, None)
        else:
            return (scholar_id, False, "Failed to fetch")
    except Exception as e:
        return (scholar_id, False, str(e))


# Main execution
if __name__ == "__main__":
    # Load all scholar IDs
    ids_file = "/sensei-fs/users/yuhli/proj_citation/citation/activate_authors_and_paper/v1/unique_scholar_ids.json"
    with open(ids_file, 'r') as f:
        all_scholar_ids = json.load(f)
    
    print(f"Loaded {len(all_scholar_ids)} scholar IDs\n")
    
    # Create output directory
    output_dir = "/sensei-fs/users/yuhli/proj_citation/citation/web_crawling/all_author_profiles"
    os.makedirs(output_dir, exist_ok=True)
    
    # Check already processed
    processed_ids = set()
    for filename in os.listdir(output_dir):
        if filename.startswith("author_") and filename.endswith(".json"):
            scholar_id = filename.replace("author_", "").replace(".json", "")
            processed_ids.add(scholar_id)
    
    print(f"Already processed: {len(processed_ids)} authors")
    print(f"Remaining: {len(all_scholar_ids) - len(processed_ids)} authors\n")
    
    # Filter out already processed IDs
    ids_to_process = [sid for sid in all_scholar_ids if sid not in processed_ids]
    
    print(f"Starting parallel processing with 10 processes...\n")
    
    # Statistics
    stats = {
        "total": len(all_scholar_ids),
        "already_processed": len(processed_ids),
        "newly_processed": 0,
        "failed": 0
    }
    
    if len(ids_to_process) == 0:
        print("All authors already processed!")
    else:
        # Use multiprocessing
        num_processes = 10
        
        with Pool(processes=num_processes) as pool:
            # Create partial function with output_dir
            process_func = partial(process_single_author, output_dir=output_dir)
            
            # Process in parallel
            results = pool.map(process_func, ids_to_process)
            
            # Count results
            for scholar_id, success, error in results:
                if success:
                    stats["newly_processed"] += 1
                else:
                    stats["failed"] += 1
                
                # Progress every 100
                total_done = stats["newly_processed"] + stats["failed"]
                if total_done % 100 == 0:
                    print(f"Progress: {total_done}/{len(ids_to_process)} (Success: {stats['newly_processed']}, Failed: {stats['failed']})")
    
    # Final statistics
    print("\n" + "="*80)
    print("FINAL STATISTICS")
    print("="*80)
    print(f"Total scholar IDs: {stats['total']}")
    print(f"Already processed: {stats['already_processed']}")
    print(f"Newly processed: {stats['newly_processed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total now: {stats['already_processed'] + stats['newly_processed']}")
    print(f"\nProfiles saved to: {output_dir}")
    
    # Save statistics
    stats_file = os.path.join(output_dir, "statistics.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to: {stats_file}")

