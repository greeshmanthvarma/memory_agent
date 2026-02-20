from openai import OpenAI
from dotenv import load_dotenv
from fastembed import SparseTextEmbedding, SparseEmbedding
import tiktoken
import os

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
sparse_embedder = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")

def sparse_embed_text(text: str) -> SparseEmbedding:
    try:
        return sparse_embedder.embed([text])[0]
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