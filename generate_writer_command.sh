#!/bin/bash

# Path to your .env file
ENV_FILE=".env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo ".env file not found!"
  exit 1
fi

# Start the command
CMD="writer deploy ."

# Read each line in .env file
while IFS= read -r line || [[ -n "$line" ]]; do
  # Ignore comments and empty lines
  if [[ "$line" == \#* ]] || [[ -z "$line" ]]; then
    continue
  fi
  
  # Add the line to the command as a --env flag
  CMD="$CMD --env $line"
done < "$ENV_FILE"

# Echo the final command
echo "$CMD"
