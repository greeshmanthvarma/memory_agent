
from app.services.embedding_service import embed_text
from app.services.memory_service import get_memory_by_query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.db_models import UserModel

def create_search_memories_tool(db: AsyncSession, user: UserModel):
    
    async def search_memories(query : str) -> str:
        """
        Search for relevant memories by semantic similarity.
        
        Use this tool when you need to recall past information, preferences, 
        or experiences that might be relevant to the current conversation.
        
        Rules:
            Memories with memory_type = "explicit" are more likely to be relevant to the current conversation.
            Memories with higher similarity scores are more likely to be relevant to the current conversation.
        
        Args:
            query: The search query to find relevant memories
            
        Returns:
            A formatted string containing relevant memories with their similarity scores.
        """

        try:
            query_vector = embed_text(query)
            results= await get_memory_by_query(query_vector,collection_name=user.collection_name,user_id=user.id,db=db)
            if len(results) == 0:
                return "No memories found."

            formatted_memories = []
            for result in results[:5]:
                memory = result["memory"]
                similarity = result["similarity"]
                tags_str = ", ".join(memory.tags) if memory.tags else "No tags"
                
                created_str = memory.created_at.strftime("%Y-%m-%d %H:%M:%S")

                current_time = datetime.now()
                time_difference = current_time - memory.created_at
                
                if time_difference < timedelta(hours=1):
                    time_str = f"{int(time_difference.total_seconds() / 60)} minutes ago"
                elif time_difference < timedelta(days=1):
                    time_str = f"{int(time_difference.total_seconds() / 3600)} hours ago"
                elif time_difference.days == 1:
                    time_str = "yesterday"
                elif time_difference.days < 7:
                    time_str = f"{time_difference.days} days ago"
                elif time_difference.days < 30:
                    time_str = f"{time_difference.days//7} weeks ago"
                elif time_difference.days < 365:
                    time_str = f"{time_difference.days // 30} months ago"
                else:
                    time_str = f"{time_difference.days // 365} years ago"
                
                formatted_memory = (f"Memory ID {memory.id}: {memory.content}\n"
                                    f"  Memory Type: {memory.memory_type}, Similarity: {similarity:.2f}\n"
                                    f"  Tags: {tags_str}, Created: {time_str} ({created_str})\n"
                                    )
                
                formatted_memories.append(formatted_memory)
            return "\n\n".join(formatted_memories)
        except Exception as e:
            return f"Error searching memories: {str(e)}"

    return search_memories