"""
One-time migration: ensure every user's Qdrant collection has dense + sparse vectors.

Run once in dev and prod after adding sparse to the schema. From repo root:
  cd backend && uv run python -m scripts.migrate_qdrant_add_sparse

Collections that already have "sparse" are skipped. Collections without sparse are
recreated with dense+sparse: points are copied (dense from existing; sparse computed
from payload content), then the user's collection_name is updated and the old
collection is deleted.
"""

import asyncio
import os
import sys

# Add backend to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from qdrant_client.models import Distance, VectorParams, SparseVectorParams
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.db_models import UserModel
from app.services.qdrant_service import (
    qdrant_client,
    build_point,
    _ensure_user_id_index,
    _ensure_is_superseded_index,
)


def collection_has_sparse(collection_name: str) -> bool:
    """Return True if points in the collection have a sparse vector (reliable for old vs new schema)."""
    try:
        records, _ = qdrant_client.scroll(
            collection_name=collection_name, limit=1, with_payload=False, with_vectors=True
        )
        if not records:
            return False  # empty → treat as no sparse so we won't migrate
        v = getattr(records[0], "vector", None) or {}
        return isinstance(v, dict) and "sparse" in v
    except Exception:
        return False


def get_dense_size(collection_name: str) -> int:
    """Return dense vector size from the first point. Default 1536."""
    try:
        records, _ = qdrant_client.scroll(
            collection_name=collection_name, limit=1, with_payload=False, with_vectors=True
        )
        if not records:
            return 1536
        v = getattr(records[0], "vector", None) or {}
        if isinstance(v, dict):
            dense = v.get("dense") or v.get(None)
        else:
            dense = v
        return len(dense) if dense else 1536
    except Exception:
        return 1536


def migrate_collection(old_name: str, new_name: str, vector_size: int) -> int:
    """Copy all points from old_name to new_name with sparse added. Returns point count."""
    qdrant_client.create_collection(
        collection_name=new_name,
        vectors_config={"dense": VectorParams(size=vector_size, distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams()},
    )
    _ensure_user_id_index(new_name)
    _ensure_is_superseded_index(new_name)

    count = 0
    offset = None
    while True:
        records, offset = qdrant_client.scroll(
            collection_name=old_name,
            limit=50,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        if not records:
            break
        for rec in records:
            payload = rec.payload or {}
            vectors = getattr(rec, "vector", None) or {}
            if isinstance(vectors, dict):
                dense = vectors.get("dense") or vectors.get(None)
            else:
                dense = vectors
            if not dense:
                continue
            try:
                point = build_point(dense, payload, id=rec.id)
                qdrant_client.upsert(collection_name=new_name, points=[point])
                count += 1
            except Exception as e:
                print(f"  Skip point {rec.id}: {e}")
        if offset is None:
            break

    return count


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UserModel.id, UserModel.collection_name))
        users = result.all()

    for (user_id, collection_name) in users:
        if not collection_name:
            continue
        if not qdrant_client.collection_exists(collection_name=collection_name):
            print(f"User {user_id}: collection {collection_name!r} does not exist, skip")
            continue
        if collection_has_sparse(collection_name):
            print(f"User {user_id}: {collection_name!r} already has sparse, skip")
            continue

        new_name = f"{collection_name}_v2"
        if qdrant_client.collection_exists(collection_name=new_name):
            print(f"User {user_id}: {new_name!r} already exists (partial migration?), skip")
            continue

        vector_size = get_dense_size(collection_name)
        print(f"User {user_id}: migrating {collection_name!r} -> {new_name!r} (vector_size={vector_size}) ...")
        n = migrate_collection(collection_name, new_name, vector_size)
        print(f"  Migrated {n} points")

        qdrant_client.delete_collection(collection_name=collection_name)
        async with AsyncSessionLocal() as db:
            row = await db.execute(select(UserModel).where(UserModel.id == user_id))
            user = row.scalar_one_or_none()
            if user:
                user.collection_name = new_name
                await db.commit()
                print(f"  Updated user {user_id} collection_name to {new_name!r}")
            else:
                print(f"  Warning: user {user_id} not found in DB")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
