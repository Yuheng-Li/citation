#!/usr/bin/env python3
"""
Analyze active authors in the field based on authorship position:
- At least 1 first or last author position, OR
- At least 3 middle author positions
"""

import os
import json
from collections import defaultdict

def analyze_active_authors():
    """Find authors who are truly active in the field"""
    
    # ========== CONFIGURATION ==========
    # Set conference filter: None for all conferences, or list of conference names
    # Examples:
    #   None - All conferences
    #   ['cvpr', 'iccv', 'eccv'] - Only CV conferences
    #   ['iclr', 'icml', 'nips'] - Only ML conferences
    #   ['acl', 'emnlp', 'naacl'] - Only NLP conferences
    CONFERENCE_FILTER = None  # Change this to filter conferences
    
    # Activity thresholds
    MIN_FIRST_OR_LAST = 2  # Minimum first or last author positions
    MIN_MIDDLE = 4  # Minimum middle author positions (if no first/last)
    # ====================================
    
    folder = 'conference_papers'
    
    # Check if folder exists
    if not os.path.exists(folder):
        print(f"Error: Folder '{folder}' does not exist!")
        return
    
    # Track authorship positions for each author
    author_stats = defaultdict(lambda: {
        'first_author': 0,
        'last_author': 0,
        'middle_author': 0,
        'total': 0
    })
    
    # Read all paper files
    all_files = sorted([f for f in os.listdir(folder) if f.endswith('.json')])
    
    # Filter files based on conference
    if CONFERENCE_FILTER:
        files = [f for f in all_files if any(f.startswith(conf.lower()) for conf in CONFERENCE_FILTER)]
        filter_text = f" ({', '.join([c.upper() for c in CONFERENCE_FILTER])})"
    else:
        files = all_files
        filter_text = " (All conferences)"
    
    if not files:
        print(f"Error: No JSON files found in '{folder}'{filter_text}")
        return
    
    print("=" * 80)
    print("Active Author Analysis" + filter_text)
    print("=" * 80)
    print("\nCriteria for 'active' author:")
    print(f"  - At least {MIN_FIRST_OR_LAST} first OR last author positions, OR")
    print(f"  - At least {MIN_MIDDLE} middle author positions")
    print("=" * 80)
    print()
    
    print(f"Reading {len(files)} conference paper files...\n")
    
    total_papers = 0
    papers_with_authors = 0
    
    for filename in files:
        filepath = os.path.join(folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                papers = json.load(f)
                total_papers += len(papers)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Skipping {filename} due to error: {e}")
            continue
        
        for paper in papers:
            authors = paper.get('authors', [])
            
            if not authors:
                continue
            
            papers_with_authors += 1
            num_authors = len(authors)
            
            for idx, author in enumerate(authors):
                # Skip empty or None author names
                if not author or not str(author).strip():
                    continue
                
                # Normalize author name (strip whitespace, handle case)
                # Note: keeping original case to preserve name formatting
                author_normalized = str(author).strip()
                
                author_stats[author_normalized]['total'] += 1
                
                if idx == 0:
                    # First author
                    author_stats[author_normalized]['first_author'] += 1
                elif idx == num_authors - 1 and num_authors > 1:
                    # Last author (only if there's more than 1 author)
                    author_stats[author_normalized]['last_author'] += 1
                else:
                    # Middle author
                    author_stats[author_normalized]['middle_author'] += 1
    
    print(f"✓ Total: {total_papers:,} papers")
    print(f"✓ Papers with authors: {papers_with_authors:,}")
    print(f"✓ Total unique authors: {len(author_stats):,}\n")
    
    if not author_stats:
        print("Error: No authors found in the papers!")
        return
    
    # Classify authors
    print("Analyzing author activity...\n")
    
    active_authors = []
    inactive_authors = []
    
    for author, stats in author_stats.items():
        # Check if author meets "active" criteria
        has_first_or_last = (stats['first_author'] >= MIN_FIRST_OR_LAST or stats['last_author'] >= MIN_FIRST_OR_LAST)
        has_enough_middle = (stats['middle_author'] >= MIN_MIDDLE)
        
        if has_first_or_last or has_enough_middle:
            active_authors.append((author, stats))
        else:
            inactive_authors.append((author, stats))
    
    # Print statistics
    print("=" * 80)
    print("Results")
    print("=" * 80)
    print(f"Active authors: {len(active_authors):,} ({len(active_authors)/len(author_stats)*100:.1f}%)")
    print(f"  - With ≥{MIN_FIRST_OR_LAST} first/last authorships: {sum(1 for a, s in active_authors if s['first_author'] >= MIN_FIRST_OR_LAST or s['last_author'] >= MIN_FIRST_OR_LAST):,}")
    print(f"  - With ≥{MIN_MIDDLE} middle authorships only: {sum(1 for a, s in active_authors if s['first_author'] < MIN_FIRST_OR_LAST and s['last_author'] < MIN_FIRST_OR_LAST and s['middle_author'] >= MIN_MIDDLE):,}")
    print()
    print(f"Inactive authors: {len(inactive_authors):,} ({len(inactive_authors)/len(author_stats)*100:.1f}%)")
    print("=" * 80)
    print()
    
    # Breakdown by criteria
    print("Detailed Breakdown:")
    print("-" * 80)
    
    # Count by different combinations
    first_or_last_count = sum(1 for a, s in active_authors if s['first_author'] >= MIN_FIRST_OR_LAST or s['last_author'] >= MIN_FIRST_OR_LAST)
    only_middle_count = sum(1 for a, s in active_authors if s['first_author'] < MIN_FIRST_OR_LAST and s['last_author'] < MIN_FIRST_OR_LAST and s['middle_author'] >= MIN_MIDDLE)
    
    first_count = sum(1 for a, s in author_stats.items() if s['first_author'] >= MIN_FIRST_OR_LAST)
    last_count = sum(1 for a, s in author_stats.items() if s['last_author'] >= MIN_FIRST_OR_LAST)
    both_count = sum(1 for a, s in author_stats.items() if s['first_author'] >= MIN_FIRST_OR_LAST and s['last_author'] >= MIN_FIRST_OR_LAST)
    
    print(f"Authors with ≥{MIN_FIRST_OR_LAST} first author positions: {first_count:,}")
    print(f"Authors with ≥{MIN_FIRST_OR_LAST} last author positions: {last_count:,}")
    print(f"Authors with both ≥{MIN_FIRST_OR_LAST} first AND last positions: {both_count:,}")
    print(f"Authors with ≥{MIN_MIDDLE} middle positions (insufficient first/last): {only_middle_count:,}")
    print("-" * 80)
    print()
    
    # Save results
    if CONFERENCE_FILTER:
        suffix = '_' + '_'.join([c.lower() for c in CONFERENCE_FILTER])
        filter_desc = f" ({', '.join([c.upper() for c in CONFERENCE_FILTER])})"
    else:
        suffix = ''
        filter_desc = " (All conferences)"
    
    output_file = f'active_authors_report{suffix}.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"Active Author Analysis Report{filter_desc}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Criteria:\n")
        f.write(f"  - At least {MIN_FIRST_OR_LAST} first OR last author positions, OR\n")
        f.write(f"  - At least {MIN_MIDDLE} middle author positions\n\n")
        
        f.write(f"Total papers: {total_papers:,}\n")
        f.write(f"Total unique authors: {len(author_stats):,}\n")
        f.write(f"Active authors: {len(active_authors):,} ({len(active_authors)/len(author_stats)*100:.1f}%)\n")
        f.write(f"Inactive authors: {len(inactive_authors):,} ({len(inactive_authors)/len(author_stats)*100:.1f}%)\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("Active Authors (sorted by total papers)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Rank':<8} {'Author Name':<50} {'Total':<8} {'First':<8} {'Last':<8} {'Middle':<8}\n")
        f.write("-" * 80 + "\n")
        
        # Sort active authors by total papers
        sorted_active = sorted(active_authors, key=lambda x: x[1]['total'], reverse=True)
        
        for i, (author, stats) in enumerate(sorted_active, 1):
            f.write(f"{i:<8} {author:<50} {stats['total']:<8} {stats['first_author']:<8} "
                   f"{stats['last_author']:<8} {stats['middle_author']:<8}\n")
    
    print(f"✓ Detailed report saved to: {output_file}")
    
    # Save active authors list (JSON)
    output_json = f'active_authors{suffix}.json'
    active_authors_data = []
    for author, stats in sorted_active:
        active_authors_data.append({
            'name': author,
            'total_papers': stats['total'],
            'first_author': stats['first_author'],
            'last_author': stats['last_author'],
            'middle_author': stats['middle_author']
        })
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(active_authors_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Active authors list saved to: {output_json}")
    
    # Show top 20 active authors
    print("\n" + "=" * 80)
    print("Top 20 Most Active Authors")
    print("=" * 80)
    print(f"{'Rank':<6} {'Author':<40} {'Total':<7} {'1st':<6} {'Last':<6} {'Mid':<6}")
    print("-" * 80)
    
    for i, (author, stats) in enumerate(sorted_active[:20], 1):
        print(f"{i:<6} {author:<40} {stats['total']:<7} {stats['first_author']:<6} "
              f"{stats['last_author']:<6} {stats['middle_author']:<6}")
    
    print("=" * 80)


if __name__ == '__main__':
    analyze_active_authors()

