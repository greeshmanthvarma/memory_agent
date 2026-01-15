from app.db_models import MemoryModel
from app.database import get_db

db=get_db()

def db_create_memory(memory: MemoryModel):
    try:
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory
    except Exception as e:
        db.rollback()
        raise Exception(f"Error creating memory: {e}")