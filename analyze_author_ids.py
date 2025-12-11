#!/usr/bin/env python3
"""
Analyze author ID frequency in gs_data_collection.json
"""
import json
import argparse
from collections import Counter

def lookup_author(papers, author_id):
    """Look up papers by a specific author ID"""
    matching_papers = []
    
    for paper in papers:
        gs_authors = paper.get('gs_authors', [])
        if author_id in gs_authors:
            matching_papers.append(paper)
    
    if not matching_papers:
        print(f"\nNo papers found for author ID: {author_id}")
        return
    
    print(f"\n" + "=" * 80)
    print(f"Author ID: {author_id}")
    print(f"Google Scholar: https://scholar.google.com/citations?user={author_id}")
    print(f"Total papers: {len(matching_papers)}")
    print("=" * 80)
    
    for i, paper in enumerate(matching_papers, 1):
        print(f"\n{i}. {paper.get('title', 'N/A')}")
        print(f"   arXiv ID: {paper.get('arxiv_id', 'N/A')}")
        print(f"   Year: {paper.get('year', 'N/A')}")
        print(f"   Citations: {paper.get('citation_count', 0)}")
        print(f"   arXiv URL: {paper.get('arxiv_url', 'N/A')}")

def main():
    parser = argparse.ArgumentParser(description='Analyze author IDs in Google Scholar data')
    parser.add_argument('--author-id', '-a', type=str, help='Look up papers by a specific author ID')
    parser.add_argument('--file', '-f', type=str, default='gs_data_collection.json', 
                        help='Input JSON file (default: gs_data_collection.json)')
    args = parser.parse_args()
    
    input_file = args.file
    
    print(f"Loading data: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    print(f"Total papers: {len(papers)}\n")
    
    # If author ID is specified, look up and exit
    if args.author_id:
        lookup_author(papers, args.author_id)
        return
    
    # Collect all author IDs
    all_author_ids = []
    papers_with_ids = 0
    
    for paper in papers:
        gs_authors = paper.get('gs_authors', [])
        if gs_authors:  # Only count papers with author IDs
            papers_with_ids += 1
            all_author_ids.extend(gs_authors)
    
    print(f"Papers with author IDs: {papers_with_ids}")
    print(f"Total author IDs (with duplicates): {len(all_author_ids)}")
    
    # Count frequency of each ID
    id_counter = Counter(all_author_ids)
    unique_ids = len(id_counter)
    
    print(f"Unique author IDs: {unique_ids}\n")
    
    # Group by frequency
    frequency_distribution = Counter(id_counter.values())
    
    # Calculate cumulative sum (authors with >= n papers)
    sorted_freqs = sorted(frequency_distribution.keys())
    cumulative_sum = {}
    for freq in sorted_freqs:
        cumulative_sum[freq] = sum(frequency_distribution[f] for f in frequency_distribution.keys() if f >= freq)
    
    print("=" * 80)
    print("Author ID Frequency Distribution:")
    print("=" * 80)
    print(f"{'Frequency':<10} {'Number of Authors':<15} {'Percentage':<12} {'>= Freq (Cumulative)':<20}")
    print("-" * 80)
    
    # Sort by frequency (from low to high)
    for count in sorted_freqs:
        num_authors = frequency_distribution[count]
        percentage = (num_authors / unique_ids) * 100
        cumulative = cumulative_sum[count]
        cumulative_pct = (cumulative / unique_ids) * 100
        print(f"{count:<10} {num_authors:<15} {percentage:>6.2f}%     {cumulative:<10} ({cumulative_pct:.2f}%)")
    
    print("=" * 80)
    
    # Most prolific authors
    max_count = max(id_counter.values())
    most_frequent = [(author_id, count) for author_id, count in id_counter.items() if count == max_count]
    
    print("\n" + "=" * 60)
    print("Most Prolific Authors (by frequency):")
    print("=" * 60)
    for author_id, count in most_frequent[:10]:  # Show top 10
        print(f"  ID: {author_id} - appears {count} times")
        print(f"    Google Scholar: https://scholar.google.com/citations?user={author_id}")

if __name__ == "__main__":
    main()


