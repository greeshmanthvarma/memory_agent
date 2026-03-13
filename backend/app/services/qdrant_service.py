from qdrant_client import QdrantClient
import requests,json
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PointIdsList,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
    SparseVectorParams,
    SparseVector,
    Prefetch,
    FusionQuery,
    Fusion,
    Document
)
import uuid
from dotenv import load_dotenv
import os
from app.services.embedding_service import sparse_embed_text

load_dotenv()

_qdrant_url = os.getenv("QDRANT_URL")
_qdrant_api_key = os.getenv("QDRANT_API_KEY")
IS_CLOUD = bool(_qdrant_api_key)

qdrant_client = QdrantClient(
    url=_qdrant_url,
    api_key=_qdrant_api_key if _qdrant_api_key else None,
    cloud_inference=True
)


def _ensure_user_id_index(collection_name: str):
    """Create payload index for user_id so filters on user_id work. Idempotent."""
    try:
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name="user_id",
            field_schema=PayloadSchemaType.INTEGER,
        )
    except Exception:
        # Index may already exist
        pass


def _ensure_is_superseded_index(collection_name: str):
    """Create payload index for is_superseded so filters work. Idempotent."""
    try:
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name="is_superseded",
            field_schema=PayloadSchemaType.BOOL,
        )
    except Exception:
        pass


def ensure_all_collection_indexes():
    """Run at startup: ensure user_id and is_superseded indexes on every existing collection. Idempotent."""
    try:
        resp = qdrant_client.get_collections()
        for col in resp.collections:
            _ensure_user_id_index(col.name)
            _ensure_is_superseded_index(col.name)
    except Exception as e:
        raise Exception(f"Error ensuring Qdrant indexes: {e}") from e


def create_collection(name: str = "memories", vector_size: int = 1536):
    try:
        if qdrant_client.collection_exists(collection_name=name):
            _ensure_user_id_index(name)
            _ensure_is_superseded_index(name)
            return qdrant_client.get_collection(collection_name=name)
        else:
            created = qdrant_client.create_collection(
                collection_name=name,
                vectors_config={
                    "dense": VectorParams(size=vector_size, distance=Distance.COSINE),
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(),
                },
            )
            _ensure_user_id_index(name)
            _ensure_is_superseded_index(name)
            return created
    except Exception as e:
        raise Exception(f"Error creating/getting collection: {e}")

def delete_collection(collection_name: str):
    try:
        qdrant_client.delete_collection(collection_name=collection_name)
    except Exception as e:
        raise Exception(f"Error deleting collection: {e}")

def build_point(dense_embedding: list[float], metadata: dict, id: uuid.UUID = None):
    content = metadata.get("content")
    if IS_CLOUD:
        sparse_vector = Document(
            text=content,
            model="qdrant/bm25"
        )
    else:
        sparse_embedding = sparse_embed_text(content)
        sparse_vector = SparseVector(
            indices=sparse_embedding.indices,
            values=sparse_embedding.values
        )
    
    return PointStruct(
        id=id or uuid.uuid4(),
        vector={
            "dense": dense_embedding,
            "sparse": sparse_vector,
        },
        payload=metadata,
    )

def add_point(collection_name: str, dense_embedding: list[float], metadata: dict, id: uuid.UUID = None):
    try:
        point = build_point(dense_embedding,metadata, id)
        qdrant_client.upsert(collection_name=collection_name,points=[point])
        return point
    except Exception as e:
        raise Exception(f"Error adding point: {e}")


def get_point_vectors(collection_name: str, point_id: uuid.UUID) -> tuple[list[float], SparseVector]:
    """Return (dense, sparse) for a point. Use when re-upserting with updated payload."""
    try:
        result = qdrant_client.retrieve(
            collection_name=collection_name,
            ids=[point_id],
            with_vectors=True,
            with_payload=False,
        )
        if not result or len(result) == 0:
            raise ValueError(f"Point {point_id} not found in collection {collection_name}")
        vectors = result[0].vector
        if not isinstance(vectors, dict):
            raise ValueError(f"Expected named vectors dict, got {type(vectors)}")
        dense = vectors["dense"]
        sparse = vectors["sparse"]
        if isinstance(sparse, dict):
            sparse = SparseVector(indices=sparse["indices"], values=sparse["values"])
        return dense, sparse
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error retrieving point vectors: {e}")


def search_points(collection_name: str, query: str, dense_query_vector: list[float], limit: int = 10, user_id: int = None):
    try:
        must_conditions = []
        if user_id is not None:
            must_conditions.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))
        must_conditions.append(FieldCondition(key="is_superseded", match=MatchValue(value=False)))
        query_filter = Filter(must=must_conditions) if must_conditions else None
        if IS_CLOUD:
            sparse_prefetch = Prefetch(
                query=Document(text=query, model="qdrant/bm25"),
                using="sparse",
                limit=40,
            )
        else:
            sparse_embedding = sparse_embed_text(query)
            sparse_prefetch = Prefetch(
                query=SparseVector(
                    indices=sparse_embedding.indices,
                    values=sparse_embedding.values,
                ),
                using="sparse",
                limit=40,
            )
        search_result = qdrant_client.query_points(
            collection_name=collection_name,
            prefetch=[
                sparse_prefetch,
                Prefetch(
                    query=dense_query_vector,
                    using="dense",
                    limit=40,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
            with_payload=True,
            query_filter=query_filter,
        )
        if not search_result.points:
            return []
        reranked_results = rerank(query, search_result, limit)
        return reranked_results
    except Exception as e:
        raise Exception(f"Error searching points: {e}")


def search_points_raw(collection_name: str, query: str, dense_query_vector: list[float], limit: int = 10, user_id: int = None):

    try:
        must_conditions = []
        if user_id is not None:
            must_conditions.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))
        must_conditions.append(FieldCondition(key="is_superseded", match=MatchValue(value=False)))
        query_filter = Filter(must=must_conditions) if must_conditions else None

        if IS_CLOUD:
            sparse_prefetch = Prefetch(
                query=Document(text=query, model="qdrant/bm25"),
                using="sparse",
                limit=40,
            )
        else:
            sparse_embedding = sparse_embed_text(query)
            sparse_prefetch = Prefetch(
                query=SparseVector(
                    indices=sparse_embedding.indices,
                    values=sparse_embedding.values,
                ),
                using="sparse",
                limit=40,
            )

        search_result = qdrant_client.query_points(
            collection_name=collection_name,
            prefetch=[
                sparse_prefetch,
                Prefetch(
                    query=dense_query_vector,
                    using="dense",
                    limit=40,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
            with_payload=True,
            query_filter=query_filter,
        )
        return search_result
    except Exception as e:
        raise Exception(f"Error searching points (raw): {e}")

def rerank(query: str, search_result, top_n: int = 10):
    documents = [point.payload["content"] for point in search_result.points]
    if not documents:
        return []
    url = "https://api.jina.ai/v1/rerank"
    jina_api_key = (os.getenv("JINA_API_KEY") or "").strip()
    if not jina_api_key:
        raise Exception("JINA_API_KEY is not set")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jina_api_key}"
    }

    data = {
        "model": "jina-reranker-v1-base-en",
        "query": query,
        "top_n": top_n,
        "documents": documents,
        "return_documents": True
    }

    print(f"[rerank] requesting jina model={data['model']} candidates={len(documents)} top_n={top_n}", flush=True)
    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results", [])
    usage_total_tokens = (payload.get("usage") or {}).get("total_tokens")
    print(f"[rerank] response results={len(results)} total_tokens={usage_total_tokens}", flush=True)
    final_result = [{"id":search_result.points[result["index"]].id, "content":result["document"], "similarity":result["relevance_score"]} for result in results]

    return final_result

def delete_points(collection_name: str, ids: list[uuid.UUID]):
    try:
        qdrant_client.delete(collection_name=collection_name, points_selector=PointIdsList(points=ids))
    except Exception as e:
        raise Exception(f"Error deleting points: {e}")


def backfill_is_superseded(collection_name: str, batch_size: int = 100) -> int:
    """Set is_superseded=False for points that don't have it. Run once per collection after adding the field. Returns number of points updated."""
    _ensure_is_superseded_index(collection_name)
    updated = 0
    offset = None
    while True:
        records, offset = qdrant_client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        ids_to_update = [
            r.id for r in records
            if r.payload.get("is_superseded") is not False
        ]
        if ids_to_update:
            qdrant_client.set_payload(
                collection_name=collection_name,
                payload={"is_superseded": False},
                points=ids_to_update,
            )
            updated += len(ids_to_update)
        if offset is None:
            break
    return updated