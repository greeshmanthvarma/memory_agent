from qdrant_client import QdrantClient
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
    PreFetch,
    FusionQuery,
    Fusion
)
import uuid
from dotenv import load_dotenv
import os
from fastembed import SparseEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

load_dotenv()

_qdrant_url = os.getenv("QDRANT_URL")
_qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_client = QdrantClient(
    url=_qdrant_url,
    api_key=_qdrant_api_key if _qdrant_api_key else None,
)
reranker = TextCrossEncoder(model_name='jinaai/jina-reranker-v1-turbo-en')
top_k_threshold = 5

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


def create_collection(name: str = "memories", vector_size: int = 1536):
    try:
        if qdrant_client.collection_exists(collection_name=name):
            _ensure_user_id_index(name)
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
            return created
    except Exception as e:
        raise Exception(f"Error creating/getting collection: {e}")

def delete_collection(collection_name: str):
    try:
        qdrant_client.delete_collection(collection_name=collection_name)
    except Exception as e:
        raise Exception(f"Error deleting collection: {e}")

def build_point(dense_embedding: list[float], sparse_embedding: SparseEmbedding, metadata: dict, id: uuid.UUID = None):
    return PointStruct(
        id=id or uuid.uuid4(),
        vector={
            "dense" : dense_embedding,
            "sparse": SparseVector(
                indices=sparse_embedding.indices,
                values=sparse_embedding.values,
            ),
        },
        
        payload=metadata,
    )

def add_point(collection_name: str, dense_embedding: list[float], sparse_embedding: SparseEmbedding, metadata: dict, id: uuid.UUID = None):
    try:
        point = build_point(dense_embedding, sparse_embedding, metadata, id)
        qdrant_client.upsert(collection_name=collection_name,points=[point])
        return point
    except Exception as e:
        raise Exception(f"Error adding point: {e}")


def get_point_vector(collection_name: str, point_id: uuid.UUID) -> list[float]:
    try:
        result = qdrant_client.retrieve(
            collection_name=collection_name,
            ids=[point_id],
            with_vectors=True,
            with_payload=False,
        )
        if not result or len(result) == 0:
            raise ValueError(f"Point {point_id} not found in collection {collection_name}")
        return result[0].vector
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error retrieving point vector: {e}")


def search_points(collection_name: str, query: str, dense_query_vector: list[float], sparse_query_vector: SparseEmbedding, limit: int = 10, user_id: int = None):
    try:
        if user_id is not None:
            _ensure_user_id_index(collection_name)
        query_filter = None
        if user_id is not None:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        search_result = qdrant_client.query_points(
            collection_name=collection_name,
            prefetch=[
                PreFetch(query=SparseVector(indices=sparse_query_vector.indices, values=sparse_query_vector.values),
                using="sparse",
                limit=20
                ),
                PreFetch(
                query=dense_query_vector,
                using="dense",
                limit=20,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
            with_payload=True,
            query_filter=query_filter,
        )
        search_result_contents = [result.payload["content"] for result in search_result.points]
        reranked_results = list (reranker.rerank(query, search_result_contents))

        ranking= [
            (index, score, search_result_contents[index]) 
            for index, score in enumerate(reranked_results)
            if score > 0.4
        ]
        ranking.sort(key=lambda x: x[1], reverse=True)
        ranking= ranking[:top_k_threshold]
        final_result = [{"id":search_result.points[index].id, "content":search_result_contents[index], "similarity":score} for index, score in ranking]


        return final_result
    except Exception as e:
        raise Exception(f"Error searching points: {e}")

def delete_points(collection_name: str, ids: list[uuid.UUID]):
    try:
        qdrant_client.delete(collection_name=collection_name, points_selector=PointIdsList(points=ids))
    except Exception as e:
        raise Exception(f"Error deleting points: {e}")