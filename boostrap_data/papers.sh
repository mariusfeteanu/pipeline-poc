#!/usr/bin/env bash
DOMAIN="${1:-cs.CL}"
XMLDIR="../.data/papers/$DOMAIN/xml"
PDFDIR="../.data/papers/$DOMAIN/pdf"
CHUNK=300
MAX_SEEN=1000

if [ -d "$PDFDIR" ]; then
  echo "Warning: $PDFDIR already exists"
  return 0
fi

if [ ! -d "$XMLDIR" ]; then
  mkdir -p "$XMLDIR"
  SEEN=0
  while [ $SEEN -lt $MAX_SEEN ]; do
    curl -sL -A "Mozilla/5.0" \
      "https://export.arxiv.org/api/query?search_query=cat:${DOMAIN}&start=${SEEN}&max_results=${CHUNK}&sortBy=submittedDate&sortOrder=descending" \
      | xmllint --xpath "//*[local-name()='entry']" - 2>/dev/null \
      | awk -v out="$XMLDIR" '
        /<entry>/ { buf=$0 ORS; filename="" }
        /<id>/ {
          if (match($0, /arxiv.org\/abs\/([^<]+)/, a)) {
            id=a[1]; gsub("/", "_", id); gsub(":", "_", id); filename=out "/" id ".xml"
          }
          buf=buf $0 ORS; next
        }
        /<\/entry>/ {
          buf=buf $0 ORS
          if (filename != "") { print buf > filename; close(filename) }
          buf=""; next
        }
        { buf=buf $0 ORS }
      '
    SEEN=$((SEEN+CHUNK))
  done
fi

mkdir -p "$PDFDIR"
for f in "$XMLDIR"/*.xml; do
  pdf=$(grep -o 'http://arxiv.org/pdf[^"]*' "$f" | head -1)
  [ -n "$pdf" ] && curl -sL -A "Mozilla/5.0" "$pdf" -o "$PDFDIR/$(basename "$f" .xml).pdf"
done
