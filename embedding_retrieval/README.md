# Paper Embedding and Retrieval

This folder contains tools for computing embeddings and performing semantic search on CV papers.

## Files

### 1. `embeddings.py`
- **Purpose**: Simple example of using BGE-M3 model
- **What it does**: Demonstrates basic embedding computation and similarity calculation
- **Usage**: `python embeddings.py`

### 2. `compute_embeddings.py`
- **Purpose**: Compute embeddings for all papers in the dataset
- **What it does**: 
  - Loads all papers from `cv_papers_20230101_to_20250531.json`
  - Computes 1024-dimensional embeddings for each paper's abstract
  - Saves embeddings to `/mnt/localssd/paper_embeddings.npy` (69149 × 1024)
  - Saves metadata to `/mnt/localssd/paper_metadata.json`
- **Usage**: `python compute_embeddings.py`
- **Time**: ~1 minute for 69,149 papers on GPU

### 3. `retrieval.py`
- **Purpose**: Retrieval example with hardcoded query
- **What it does**: 
  - Loads pre-computed embeddings
  - Computes embedding for a query abstract
  - Returns top-10 most similar papers
- **Usage**: `python retrieval.py`
- **Note**: Edit the `query` variable in the code to search for different papers

## Workflow

1. **First time setup**: Run `compute_embeddings.py` to generate embeddings
2. **Search papers**: Use `retrieval.py` to find similar papers (edit the query in the code)

## Data Files

- **Input**: `../cv_papers_20230101_to_20250531.json` (69,149 papers)
- **Output**: 
  - `/mnt/localssd/paper_embeddings.npy` (136 MB, float16)
  - `/mnt/localssd/paper_metadata.json` (24 MB)

## Model

- **Model**: BGE-M3 (`BAAI/bge-m3`)
- **Embedding dimension**: 1024
- **Device**: CUDA (GPU)
- **Precision**: FP16

