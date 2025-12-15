#!/bin/bash

# Run Semantic Scholar extraction
# Using official API - no blocking issues!

LOG_FILE="semantic_scholar_$(date +%Y%m%d_%H%M%S).log"

echo "Starting Semantic Scholar extraction..."
echo "Logging to: $LOG_FILE"
echo ""

python -u semantic_scholar_extract.py 2>&1 | tee "$LOG_FILE"


