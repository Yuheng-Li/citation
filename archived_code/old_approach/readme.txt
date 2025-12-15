This is the original old approach (called Approach 1)

Below is from Slack: 

----------------------------------------------------------------------------------------------------------------------------------
Approach 1:
Step1: Crawled 46k papers from 9 conference (cvpr, iccv ...) over 3 years. And selected around 20k names that are active in this field (active criteria not important here, can change later).
Step2: Find those people's google scholar IDs (api cost 1.5 dollars per 1k)
Step3: Find those people's google profile which includes their papers, citations etc (api cost 1 dollar per 100 ..... yeah this step is very expensive)
Step4: Download paper / abstract for all papers in all 20k users profile
Step5: After having paper's content (such as pdf etc), then we can do whatever analysis we want
so far, we stuck at Step4. because two reasons:
there is no single source we can download all papers, the actual distribution of all papers are really random and chaos. Around 40% can be found in arxiv.
Even if we accept only arxiv paper, another problem is maintenance. Suppose we want to update this system every quarter, then we need to repeat Step3 again to get each person's latest papers, which is very costly      
----------------------------------------------------------------------------------------------------------------------------------


Code Locations:

Step 1: Code is in the folder `crawling_papers_from_proceeding`

Between Step 1 and Step 2: The folder `activate_authors_and_paper` contains code for finding the minimal set to reduce API calling times

Step 2: Code is in the folder `crawling_ids`

Step 3: Code is outside this archived folder, as it is still used by the latest approach

