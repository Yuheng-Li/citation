Below is from Slack message


----------------------------------------------------------------------------------------------------------------------------------

Here is some summary about recent progress:

Approach 1:
Step1: Crawled 46k papers from 9 conference (cvpr, iccv ...) over 3 years. And selected around 20k names that are active in this field (active criteria not important here, can change later).
Step2: Find those people's google scholar IDs (api cost 1.5 dollars per 1k)
Step3: Find those people's google profile which includes their papers, citations etc (api cost 1 dollar per 100 ..... yeah this step is very expensive)
Step4: Download paper / abstract for all papers in all 20k users profile
Step5: After having paper's content (such as pdf etc), then we can do whatever analysis we want
so far, we stuck at Step4. because two reasons:
there is no single source we can download all papers, the actual distribution of all papers are really random and chaos. Around 40% can be found in arxiv.
Even if we accept only arxiv paper, another problem is maintenance. Suppose we want to update this system every quarter, then we need to repeat Step3 again to get each person's latest papers, which is very costly      


Because of above issues, Thao and I discussed another approach.
Approach 2:
Step1: crawl all arxiv paper in AI field to get title/authors/pdf etc. However, we only know authors' "name" without knowing unique ID (which means we cannot process duplicated name issue. Good news is: this step is free! because arxiv has free api)
Step2: for each arxiv paper, there is a google scholar link. we can use this link to find authors's google scholar ID (1.5 dollars per 1k request)
Step3: then we have everything, do analysis
There is some assumption for this approach, for step1, we are basically saying arxiv has every paper we want, which I think it is ok. This can also make our system update very easy. because we can just crawl new arix papers each time in arxiv daily. Of course, if we accept this, then we also should not think reason1 in appraoch 1 is a issue. So main advantage for Approach 2 is easy and cheap to maintain.   But this approach also has two issues:
google scholar link (step2) cannot return full author list due to HTML display limit. For example here, it did not show Bolei and my name.
This is paper-first approach, which means we don't know who should be considered. (I am not sure how messy will be.)
Let me know if you have any comments

----------------------------------------------------------------------------------------------------------------------------------


## Folder Purpose

This folder contains scripts for testing paper download coverage from author profiles (Approach 1).

## Current Status

**Archived** - The project has moved to Approach 2 (paper-first approach using arXiv API).

The two files in this folder (`test_arxiv_coverage.py` and `test_semantic_scholar_coverage.py`) were used to test the paper download rate for each author profile. These scripts helped evaluate the feasibility of Approach 1, which was ultimately abandoned due to:
- High API costs for Google Scholar profile crawling
- Maintenance complexity for quarterly updates
- Limited paper coverage (only ~40% found on arXiv)
