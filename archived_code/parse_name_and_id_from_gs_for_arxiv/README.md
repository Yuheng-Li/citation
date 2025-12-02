# Parse Name and ID from Google Scholar for arXiv Papers

This folder contains archived code for parsing author names and Google Scholar IDs from Google Scholar search results for arXiv papers.

## Overview

The code in this folder was used to:
1. Fetch Google Scholar search results for arXiv papers
2. Extract author names and their Google Scholar profile IDs from the HTML
3. Match author names between arXiv and Google Scholar to verify correctness

## Files

- `fetch_gs_data_for_arxiv.py`: Main script to fetch Google Scholar data for a sample of arXiv papers
- `name_matcher.py`: Utility for matching author names between arXiv and Google Scholar (handles abbreviations, name variations, etc.)
- `test_author_matching.py`: Script to test and analyze the accuracy of author name matching
- `gs_data_collection.json`: Collected Google Scholar data for arXiv papers

## Important Note: Why This Approach Was Deprecated

**We decided to stop parsing author names** due to numerous issues encountered:

1. **Wrong last author name**: The last author in the list was often incorrectly parsed or matched
2. **Order mismatch**: Author order between arXiv and Google Scholar didn't always align correctly
3. **Missing IDs for last authors**: The last author's Google Scholar ID was frequently missing or incorrectly extracted
4. **Name parsing complexity**: Author names have many variations (abbreviations, middle names, different formats) making reliable matching difficult

## New Approach: Parse IDs Only

Instead of parsing names, **we now only parse Google Scholar IDs**, which have a very clear and reliable regex pattern:
