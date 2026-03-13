
import os
from haystack_integrations.components.embedders.fastembed import FastembedSparseTextEmbedder


cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model_cache"))
os.makedirs(cache_dir, exist_ok=True)

print("Downloading SPLADE model into:", cache_dir)
embedder = FastembedSparseTextEmbedder(
    model="prithivida/Splade_PP_en_v1",
    cache_dir=cache_dir,
)

_ = embedder.run("warm up")["sparse_embedding"]
print("Done.")