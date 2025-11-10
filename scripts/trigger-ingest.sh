#!/usr/bin/env bash
LIMIT="${1:-10}"
DOMAIN="${2:-physics.pop-ph}"
TYPE="${3:-pdf}"
DIR=".data/papers/$DOMAIN/$TYPE"
URL="http://localhost:8000/document/v1"


count=0

find "$DIR" -type f -name "*.${TYPE}" | while read -r file; do
  if (( count >= LIMIT )); then
    echo -e "Reached limit of $LIMIT files."
    break
  fi

  json_body=$(jq -n \
    --arg path "$file" \
    --arg type "$TYPE" \
    '{path: $path, file_type: $type, file_source: "arxiv"}'
  )

  echo "Posting: $file"
  curl --silent --show-error --fail --request POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$json_body"

  ((count++))
done
