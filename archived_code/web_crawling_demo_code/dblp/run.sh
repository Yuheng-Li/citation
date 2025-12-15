#!/bin/bash

# Run DBLP batch extraction and save output to log
# Both stdout and stderr are captured
# Output is shown in terminal AND saved to file

LOG_FILE="dblp_extract_$(date +%Y%m%d_%H%M%S).log"

echo "Starting DBLP batch extraction..."
echo "Logging to: $LOG_FILE"
echo ""

python -u batch_extract.py 2>&1 | tee "$LOG_FILE"


