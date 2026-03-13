from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
import os
from haystack_integrations.components.embedders.fastembed import (
    FastembedSparseTextEmbedder,
)
from haystack.dataclasses import SparseEmbedding

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "model_cache"))
_sparse_embedder = None
DISABLE_LOCAL_SPLADE = os.getenv("DISABLE_LOCAL_SPLADE", "false").lower() == "true"

def _get_sparse_embedder():
    """Lazy-init SPLADE embedder, unless explicitly disabled via env."""
    global _sparse_embedder
    if DISABLE_LOCAL_SPLADE:
        raise RuntimeError("Local SPLADE disabled via DISABLE_LOCAL_SPLADE")
    if _sparse_embedder is None:
        _sparse_embedder = FastembedSparseTextEmbedder(
            model="prithivida/Splade_PP_en_v1",
            cache_dir=cache_dir,
        )
    return _sparse_embedder

def sparse_embed_text(text: str) -> SparseEmbedding:
    try:
        result = _get_sparse_embedder().run(text)["sparse_embedding"]
        return result
    except Exception as e:
        raise Exception(f"Error sparse embedding text: {e}")

def embed_text(text: str) -> list[float]:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens= encoding.encode(text)
        if len(tokens) > 1500:
            raise Exception("Text is too long. Maximum length is 1500 tokens.")
        embedding = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return embedding.data[0].embedding
    except Exception as e:
        raise Exception(f"Error embedding text: {e}")