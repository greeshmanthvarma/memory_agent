from app.services.llm_service import build_graph
import os
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

async def compile_graph():
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        raise RuntimeError("DATABASE_URL is required for checkpointing")
    # Checkpointer expects plain postgresql:// URI, not postgresql+asyncpg://
    checkpointer_conn = conn_string.replace("postgresql+asyncpg://", "postgresql://", 1)
    try:
        pool = AsyncConnectionPool(
            checkpointer_conn,
            max_size=10,
            open=False,
            kwargs={"autocommit": True},
        )
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        builder = build_graph()
        graph = builder.compile(checkpointer=checkpointer)
    except Exception as e:
        print(f"Error compiling graph: {e}", flush=True)
        raise e
    return graph,pool