#!/bin/bash
# Create model_cache.tar.xz for EB deploy (smaller than .tar.gz = faster download, less timeout risk).
# Produces: backend/model_cache.tar.xz (contains top-level model_cache/ folder)
# Upload to S3: model_cache/model_cache.tar.xz
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d "model_cache" ]; then
  echo "model_cache/ not found in $ROOT_DIR"
  echo "Populate it first (download SPLADE + Jina reranker), then rerun."
  exit 1
fi

echo "Creating model_cache.tar.xz from $ROOT_DIR/model_cache (this may take a few minutes)..."
tar -cJf model_cache.tar.xz model_cache
echo "Wrote: $ROOT_DIR/model_cache.tar.xz"
ls -lh model_cache.tar.xz
