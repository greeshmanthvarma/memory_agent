
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastembed.rerank.cross_encoder import TextCrossEncoder

cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model_cache"))
os.makedirs(cache_dir, exist_ok=True)
print("Downloading Jina reranker into:", cache_dir)
reranker = TextCrossEncoder(
    model_name="jinaai/jina-reranker-v1-turbo-en",
    cache_dir=cache_dir,
)
_ = list(reranker.rerank("test query", ["doc one", "doc two"]))
print("Done.")
