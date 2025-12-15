#!/bin/bash

# Run batch extraction and save output to log
# Both stdout and stderr are captured
# Output is shown in terminal AND saved to file

LOG_FILE="scholar_extract_$(date +%Y%m%d_%H%M%S).log"

echo "Starting batch extraction..."
echo "Logging to: $LOG_FILE"
echo ""

python -u batch_extract.py 2>&1 | tee "$LOG_FILE"



