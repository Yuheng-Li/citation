#!/usr/bin/env python3
"""Analyze all unique authors across all conference papers"""

import os
import json
from collections import Counter

def analyze_authors():
    """Analyze all unique authors across all conference papers"""
    
    folder = 'conference_papers'
    all_authors = []
    
    # Read all paper files
    files = sorted([f for f in os.listdir(folder) if f.endswith('.json')])
    
    print(f"Reading {len(files)} conference paper files...\n")
    
    total_papers = 0
    for filename in files:
        filepath = os.path.join(folder, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            papers = json.load(f)
            total_papers += len(papers)
            
            # Extract all authors
            for paper in papers:
                authors = paper.get('authors', [])
                all_authors.extend(authors)
    
    print(f"✓ Total: {total_papers:,} papers")
    print(f"✓ Total: {len(all_authors):,} author entries\n")
    
    # Count occurrences of each author
    author_counts = Counter(all_authors)
    
    # Sort by count (high to low)
    sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Statistics
    unique_authors = len(author_counts)
    single_paper_authors = sum(1 for count in author_counts.values() if count == 1)
    two_paper_authors = sum(1 for count in author_counts.values() if count == 2)
    
    print("=" * 80)
    print("Statistics")
    print("=" * 80)
    print(f"Total unique authors: {unique_authors:,}")
    print(f"Authors with only 1 paper: {single_paper_authors:,} ({single_paper_authors/unique_authors*100:.1f}%)")
    print(f"Authors with only 2 papers: {two_paper_authors:,} ({two_paper_authors/unique_authors*100:.1f}%)")
    print(f"Average papers per author: {len(all_authors)/unique_authors:.2f}")
    print()
    

    
    # Save to txt file
    output_file = 'author_statistics.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("Conference Paper Author Statistics\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total papers: {total_papers:,}\n")
        f.write(f"Total author entries: {len(all_authors):,}\n")
        f.write(f"Unique authors: {unique_authors:,}\n")
        f.write(f"Authors with only 1 paper: {single_paper_authors:,} ({single_paper_authors/unique_authors*100:.1f}%)\n")
        f.write(f"Authors with only 2 papers: {two_paper_authors:,} ({two_paper_authors/unique_authors*100:.1f}%)\n")
        f.write(f"Average papers per author: {len(all_authors)/unique_authors:.2f}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("All Authors Sorted by Paper Count\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Rank':<8} {'Author Name':<60} {'Papers':<10}\n")
        f.write("-" * 80 + "\n")
        
        for i, (author, count) in enumerate(sorted_authors, 1):
            f.write(f"{i:<8} {author:<60} {count:<10}\n")
    
    print()
    print(f"✓ Full statistics saved to: {output_file}")
    
    # Paper count distribution
    print("\nPaper Count Distribution:")
    print("-" * 40)
    distribution = Counter(author_counts.values())
    for papers_count in sorted(distribution.keys())[:10]:
        author_count = distribution[papers_count]
        print(f"{papers_count:2d} papers: {author_count:6,} authors")
    
    if len(distribution) > 10:
        print("...")
        # Show last few entries
        for papers_count in sorted(distribution.keys())[-3:]:
            author_count = distribution[papers_count]
            print(f"{papers_count:2d} papers: {author_count:6,} authors")


if __name__ == '__main__':
    analyze_authors()

