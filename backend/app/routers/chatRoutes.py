from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.models import Message, MessageCreate, ConversationRead, ConversationCreate, SummarizeRequest, MemoryCreate
from app.services.llm_service import chat as chat_service, summarize_conversation as summarize_conversation_service
from app.middleware.auth import get_current_user
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import create_memory as create_memory_service
from app.services.embedding_service import embed_text
from typing import List
from app.db_models import UserModel, MessageModel, ConversationModel
from app.services.db_service import db_create_message, db_create_conversation, db_get_conversation, db_get_conversation_messages, db_get_all_conversations as db_get_all_conversations_service

chat_router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@chat_router.post("/")
async def chat(user_message: str, conversation_id: int, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        await db_get_conversation(conversation_id, user.id, db) #ensures the conversation exists and is owned by the user
        existing_messages = await db_get_conversation_messages(conversation_id, db)

        user_query = MessageModel(
            content=user_message,
            role = "user",
            conversation_id=conversation_id
        )

        user_query_response = await db_create_message(user_query, db)

        messages_list= [
            Message(
                id= m.id,
                content=m.content,
                role=m.role,
                created_at=m.created_at,
                updated_at=m.updated_at
            ) for m in existing_messages
        ]+[
            Message(
                id=user_query_response.id,
                content=user_query_response.content,
                role=user_query_response.role,
                created_at=user_query_response.created_at,
                updated_at=user_query_response.updated_at
            )
        ]
        
        response = await chat_service(user=user, db=db, user_message=user_message, messages=messages_list)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to formulate a response")
        
        assistant_response = MessageModel(
            content=response,
            role="assistant",
            conversation_id=conversation_id
        )
        await db_create_message(assistant_response, db)
        return JSONResponse({"response": response})
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
        conversation = ConversationCreate(
            id=conversation_response.id,
            title=conversation_response.title or None,
            messages=[],
            user_id=conversation_response.user_id,
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
                tags=request.tags,
            )
            created_memory = await create_memory_service(memory,embedding,user.id,user.collection_name,db)


            return JSONResponse({
                "summary": summary,
                "message":"Memory created successfully",
                "memory": created_memory.model_dump(mode='json'),
                "memory_created": True,
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
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        return JSONResponse({"conversation": conversation_read.model_dump(mode='json')})
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
                created_at=c.created_at,
                updated_at=c.updated_at
            ) for c in conversations
        ]
        return JSONResponse({"conversations": [c.model_dump(mode='json') for c in conversations_list]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

