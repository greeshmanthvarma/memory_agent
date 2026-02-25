import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.models import Message, MessageCreate, ConversationRead, ConversationCreate, SummarizeRequest, MemoryCreate, ChatRequest, ConversationUpdate, TitleFromMessageRequest
from app.services.llm_service import chat as chat_service, summarize_conversation as summarize_conversation_service, get_title as get_title_service
from app.middleware.auth import get_current_user
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import create_memory as create_memory_service
from app.services.embedding_service import embed_text
from typing import List
from app.db_models import UserModel, MessageModel, ConversationModel
from app.services.db_service import db_create_message, db_create_conversation, db_get_conversation, db_get_conversation_messages, db_get_all_conversations as db_get_all_conversations_service, db_delete_conversation as db_delete_conversation_service, db_update_conversation as db_update_conversation_service

chat_router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)

@chat_router.post("/")
async def chat(request: ChatRequest, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        conversation = await db_get_conversation(request.conversation_id, user.id, db)
        thread_id = getattr(conversation, "thread_id", None) or f"{user.id}_{request.conversation_id}"

        user_query = MessageModel(
            content=request.user_message,
            role="user",
            conversation_id=request.conversation_id,
        )
        await db_create_message(user_query, db)

        async def stream():
            full = []
            try:
                async for chunk in chat_service(
                    user=user,
                    user_message=request.user_message,
                    thread_id=thread_id,
                ):
                    full.append(chunk)
                    yield chunk
                    await asyncio.sleep(0)
            finally:
                if full:
                    text = "".join(full)
                    assistant_response = MessageModel(
                        content=text,
                        role="assistant",
                        conversation_id=request.conversation_id,
                    )
                    await db_create_message(assistant_response, db)

        return StreamingResponse(
            stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chatting: {str(e)}")



@chat_router.post("/conversation")
async def create_conversation(user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        conversation_model = ConversationModel(
            user_id=user.id
        )
        conversation_response = await db_create_conversation(conversation_model, db)
        thread_id = f"{user.id}_{conversation_response.id}"
        conversation_response.thread_id = thread_id
        await db.commit()
        await db.refresh(conversation_response)
        conversation = ConversationCreate(
            id=conversation_response.id,
            title=conversation_response.title or None,
            messages=[],
            user_id=conversation_response.user_id,
            thread_id=conversation_response.thread_id,
            created_at=conversation_response.created_at,
            updated_at=conversation_response.updated_at
        )
        return JSONResponse({"conversation": conversation.model_dump(mode='json')})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")

@chat_router.post("/conversation/summarize")
async def summarize_conversation( request: SummarizeRequest, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:

        if len(request.messages) == 0:
            raise HTTPException(status_code=400, detail="No messages provided")

        if request.conversation_id:
            await db_get_conversation(request.conversation_id, user.id, db) #ensures the conversation exists and is owned by the user
        
        summary = summarize_conversation_service(request.messages)

        if not summary or not summary.get("summary_short"):
            if request.create_memory:
                raise HTTPException(status_code=400, detail="No meaningful summary could be created")
            
            return JSONResponse({
                "summary": None,
                "message":"No memory could be extracted from this conversation",
                "memory": None,
                "memory_created": False,
            })


        memory = None

        if request.create_memory:

            embedding = embed_text(summary["summary_short"])
            memory = MemoryCreate(
                content=summary["summary_short"],
                summary_long=summary["summary_long"],
                memory_type="implicit",
                conversation_id=request.conversation_id,
                tags=summary.get("tags", []),
                memory_category=summary.get("memory_category"),
            )
            result = await create_memory_service(memory,embedding,user.id,user.collection_name,db)
            
            if result["is_duplicate"]:
                if result["duplicate_type"] == "exact":
                    message = "Memory already exists (exact match found)"
                else:
                    message = "Similar memory already exists"
            else:
                message = "Memory created successfully"

            return JSONResponse({
                "summary": summary,
                "message": message,
                "memory": result["memory"].model_dump(mode='json'),
                "memory_created": not result["is_duplicate"],
                "is_duplicate": result["is_duplicate"]
            })
        else:
            return JSONResponse({
                "summary": summary,
                "message":"Memory not created",
                "memory": None,
                "memory_created": False,
            })
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing conversation: {str(e)}")

@chat_router.get("/conversation/{conversation_id}/messages")
async def get_chat_history(conversation_id: int, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        await db_get_conversation(conversation_id, user.id, db) #ensures the conversation exists and is owned by the user
        messages = await db_get_conversation_messages(conversation_id, db)
        messages_list=[
            Message(
                id=m.id,
                content=m.content,
                role=m.role,
                created_at=m.created_at,
                updated_at=m.updated_at
            ) for m in messages
        ]
        return JSONResponse({"messages": [m.model_dump(mode='json') for m in messages_list]})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/conversation/all")
async def get_all_conversations(user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        conversations = await db_get_all_conversations_service(user.id, db)
        conversations_list=[
            ConversationRead(
                id=c.id,
                title=c.title or None,
                memory_id=c.memory_id or None,
                messages=[],
                user_id=c.user_id,
                thread_id=c.thread_id or None,
                created_at=c.created_at,
                updated_at=c.updated_at
            ) for c in conversations
        ]
        return JSONResponse({"conversations": [c.model_dump(mode='json') for c in conversations_list]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: int, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        conversation = await db_get_conversation(conversation_id, user.id, db)
        conversation_read = ConversationRead(
            id=conversation.id,
            title=conversation.title or None,
            memory_id=conversation.memory_id or None,
            messages=[],
            user_id=conversation.user_id,
            thread_id=conversation.thread_id or None,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        return JSONResponse({"conversation": conversation_read.model_dump(mode='json')})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: int, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        await db_delete_conversation_service(conversation_id, user.id, db)
        return JSONResponse({"message": "Conversation deleted successfully"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.put("/conversation/{conversation_id}")
async def update_conversation(conversation_id: int, update: ConversationUpdate, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        if update.title is None:
            raise HTTPException(status_code=400, detail="Title is required")
        await db_update_conversation_service(conversation_id, update.title, user.id, db)
        return JSONResponse({"message": "Conversation title updated successfully"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/conversation/{conversation_id}/title")
async def update_conversation_title(conversation_id: int, body: TitleFromMessageRequest, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        await db_get_conversation(conversation_id, user.id, db) #ensures the conversation exists and is owned by the user, returns ValueError if not found
        title = get_title_service(body.first_message)
        await db_update_conversation_service(conversation_id, title, user.id, db)
        return JSONResponse({"title": title})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))