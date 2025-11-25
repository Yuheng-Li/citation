#!/usr/bin/env python3
"""
Extract Google Scholar IDs for professors by specific conferences
Only saves simple txt format
"""

import csv

# Conference categories based on CSRankings taxonomy
CONFERENCE_CATEGORIES = {
    'Vision': ['cvpr', 'iccv', 'eccv'],
    'ML': ['icml', 'iclr', 'nips', 'kdd'],
    'AI': ['aaai', 'ijcai'],
    'NLP': ['acl', 'emnlp', 'naacl'],
    'IR': ['sigir', 'www']
}

# Flatten all conferences for validation
ALL_CONFERENCES = set()
for conferences in CONFERENCE_CATEGORIES.values():
    ALL_CONFERENCES.update(conferences)

def extract_by_conferences(conferences, output_file, min_papers_total=1, min_papers_after=None):
    """
    Extract professors who published in specified conferences
    
    Args:
        conferences: list of conference names (e.g., ['cvpr', 'iclr'])
        output_file: output filename (e.g., 'cvpr_iclr_scholars.txt')
        min_papers_total: minimum total number of papers required (default: 1)
        min_papers_after: tuple (min_count, year_threshold), e.g., (2, 2023) means 
                         >= 2 papers published in or after 2023 (default: None)
    """
    print(f"Extracting professors from conferences: {', '.join(conferences)}")
    print(f"Minimum total papers required: {min_papers_total}")
    if min_papers_after:
        print(f"Additional filter: >= {min_papers_after[0]} papers after year {min_papers_after[1]}")
    
    # Make sure clone this: https://github.com/emeryberger/CSRankings  
    csrankings_dir = "/sensei-fs/users/yuhli/proj_citation/CSrankings"
    
    # Verify all defined conferences exist in CSRankings data
    print("\n[0/3] Validating conferences...")
    existing_areas = set()
    with open(f"{csrankings_dir}/generated-author-info.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_areas.add(row['area'])
    
    # Check if all our defined conferences exist
    missing_conferences = ALL_CONFERENCES - existing_areas
    assert len(missing_conferences) == 0, \
        f"ERROR: The following conferences are not found in CSRankings data: {missing_conferences}"
    

    
    # 1. Find professors who published in these conferences
    print("\n[1/3] Loading publication data...")
    prof_counts = {}  # name -> total paper count in target conferences
    prof_counts_after = {}  # name -> paper count after specified year
    
    with open(f"{csrankings_dir}/generated-author-info.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['area'] in conferences:
                name = row['name']
                count = float(row['count']) if row['count'] else 0
                year = int(row['year']) if row['year'] else 0
                
                prof_counts[name] = prof_counts.get(name, 0) + count
                
                # Count papers after specified year
                if min_papers_after and year >= min_papers_after[1]:
                    prof_counts_after[name] = prof_counts_after.get(name, 0) + count
    
    # Filter by minimum papers
    target_profs = set()
    for name, count in prof_counts.items():
        if count >= min_papers_total:
            # If min_papers_after is specified, also check that condition
            if min_papers_after:
                count_after = prof_counts_after.get(name, 0)
                if count_after >= min_papers_after[0]:
                    target_profs.add(name)
            else:
                target_profs.add(name)
    
    print(f"   Found {len(target_profs)} professors matching all criteria")
    
    # 2. Get their Scholar IDs
    print("\n[2/3] Matching Scholar IDs...")
    result = {}  # name -> scholar_id
    
    with open(f"{csrankings_dir}/csrankings.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            if name in target_profs:
                scholarid = row['scholarid']
                if scholarid and scholarid != 'NOSCHOLARPAGE' and scholarid.strip():
                    result[name] = scholarid
    
    print(f"   {len(result)} professors have Scholar IDs")
    print(f"   {len(target_profs) - len(result)} professors without Scholar IDs")
    
    # 3. Save to txt (sorted by paper count, descending)
    print(f"\n[3/3] Saving to {output_file}...")
    
    # Create list of (name, scholar_id, paper_count, paper_count_after) and sort by paper count
    prof_list = []
    for name, scholar_id in result.items():
        paper_count = prof_counts.get(name, 0)
        paper_count_after = prof_counts_after.get(name, 0) if min_papers_after else None
        prof_list.append((name, scholar_id, paper_count, paper_count_after))
    
    # Sort by paper count (descending)
    prof_list.sort(key=lambda x: x[2], reverse=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for name, scholar_id, paper_count, paper_count_after in prof_list:
            if min_papers_after:
                f.write(f"{name}\t{scholar_id}\t{paper_count:.1f}\t{paper_count_after:.1f}\n")
            else:
                f.write(f"{name}\t{scholar_id}\t{paper_count:.1f}\n")
    
    print(f"\n✓ Done! Saved {len(result)} professors to {output_file}")
    print(f"   Sorted by paper count (descending)")
    if min_papers_after:
        print(f"   Format: name\\tscholar_id\\ttotal_papers\\tpapers_after_{min_papers_after[1]}")
    




def main():

    
    print("\nAvailable conference categories:")
    for category, confs in CONFERENCE_CATEGORIES.items():
        print(f"  {category:10s}: {', '.join(confs)}")
    
    # Example: Extract professors with >= 1 total paper AND >= 2 papers after 2023
    extract_by_conferences(
        conferences=['cvpr', 'iccv', 'eccv','icml', 'iclr', 'nips','acl', 'emnlp', 'naacl'],
        output_file='prof.txt',
        min_papers_total=5,
        min_papers_after=(5, 2020)  # >= 2 papers published in or after 2023
    )
    





if __name__ == '__main__':
    main()

