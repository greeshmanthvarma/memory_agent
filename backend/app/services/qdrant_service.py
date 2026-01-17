from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PointIdsList, Filter, FieldCondition, FieldMatch
import uuid
from dotenv import load_dotenv

import os

load_dotenv()

qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"))

def create_collection(name: str = "memories", vector_size: int = 1536):
    try:
        if qdrant_client.collection_exists(collection_name=name):
            return qdrant_client.get_collection(collection_name=name)
        else:
            return qdrant_client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
    except Exception as e:
        raise Exception(f"Error creating/getting collection: {e}")

def delete_collection(collection_name: str):
    try:
        qdrant_client.delete_collection(collection_name=collection_name)
    except Exception as e:
        raise Exception(f"Error deleting collection: {e}")

def build_point(embedding: list[float], metadata: dict, id: uuid.UUID = None):
    return PointStruct(
        id=id or uuid.uuid4(),
        vector=embedding,
        payload=metadata,
    )

def add_point(collection_name: str, embedding: list[float], metadata: dict, id: uuid.UUID = None):
    try:
        point = build_point(embedding, metadata, id)
        qdrant_client.upsert(collection_name=collection_name,points=[point])
        return point
    except Exception as e:
        raise Exception(f"Error adding point: {e}")


def search_points(collection_name: str, query_vector: list[float], limit: int = 10,user_id: int = None):
    try:
        query_filter = None
        if user_id is not None:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=FieldMatch(
                            value=user_id
                        )
                    )
                ]
            )
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
            query_filter=query_filter,
        )
        return [{**point.payload,"similarity":point.score, "id":point.id} for point in search_result]
    except Exception as e:
        raise Exception(f"Error searching points: {e}")

def delete_points(collection_name: str, ids: list[uuid.UUID]):
    try:
        qdrant_client.delete(collection_name=collection_name, points_selector=PointIdsList(points=ids))
    except Exception as e:
        raise Exception(f"Error deleting points: {e}")