#!/usr/bin/env bash

MANIFEST_URL="https://www.eia.gov/opendata/bulk/manifest.txt"
MANIFEST_FILE="manifest.json"
[ -f "$MANIFEST_FILE" ] || curl -s -L -A "Mozilla/5.0" "$MANIFEST_URL" | jq . > "$MANIFEST_FILE"

DATASETS_FILE="datasets"
mkdir -p ../.data

while read -r dataset; do
    [ -z "$dataset" ] && continue
    url=$(jq -r ".dataset[\"$dataset\"].accessURL" "$MANIFEST_FILE")
    if [ -z "$url" ] || [ "$url" = "null" ]; then
        echo "No URL found for $dataset"
        continue
    fi

    zipfile="../.data/$(basename "$url")"
    target_dir="../.data/$dataset"

    if [ -d "$target_dir" ] || [ -f "$zipfile" ]; then
        echo "Skipping downloading $dataset (already extracted in $target_dir)"
    else
        echo "Downloading $dataset..."
        curl -L -A "Mozilla/5.0" -o "$zipfile" "$url"
    fi

    if [ -d "$target_dir" ]; then
        echo "Skipping extracting $dataset (already extracted in $target_dir)"
    else
        echo "Extracting $dataset..."
        mkdir -p "$target_dir"
        unzip -q "$zipfile" -d "$target_dir"
    fi

done < "$DATASETS_FILE"

du -h ../.data

