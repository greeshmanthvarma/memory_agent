# Mutative memory agentic loop – step-by-step action plan



---

## Phase 1: Schema and archive

- [ ] **1.1** Add `superseded_by_id` to `MemoryModel` in [backend/app/db_models.py](backend/app/db_models.py): `Column(Integer, ForeignKey("memories.id"), nullable=True, index=True)`.
- [ ] **1.2** Create and run a migration (or run raw SQL): `ALTER TABLE memories ADD COLUMN superseded_by_id INTEGER REFERENCES memories(id);`
- [ ] **1.3** In [backend/app/services/db_service.py](backend/app/services/db_service.py): add `db_update_memory_superseded_by(memory_id, superseded_by_id, user_id, db)`.
- [ ] **1.4** In all memory read functions (`db_get_memory_by_embedding_id`, `db_get_all_memories`, etc.): add filter `MemoryModel.superseded_by_id == None` so archived memories are never returned. For the apply-update flow, keep a way to load a memory by id (to supersede it) without that filter.

---

## Phase 2: Pending updates (user confirmation)

- [ ] **2.1** Add DB model for pending memory updates (e.g. table `pending_memory_updates`: id, user_id, memory_id, new_content, reason, conversation_id optional, created_at). Add to [backend/app/db_models.py](backend/app/db_models.py).
- [ ] **2.2** In db_service: add create/get/delete helpers for pending updates.
- [ ] **2.3** Add endpoint `POST /api/chat/memory-updates/apply` (body: pending_update_id or memory_id + new_content). It loads pending row, validates user, calls `update_memory_supersede`, then deletes the pending row. Add to chatRoutes or a new router.
- [ ] **2.4** Add endpoint `POST /api/chat/memory-updates/cancel` (body: pending_update_id) to delete the pending row. Optional if frontend can just drop the UI.

---

## Phase 3: Memory service

- [ ] **3.1** In [backend/app/services/memory_service.py](backend/app/services/memory_service.py): add optional parameter `min_similarity` (default None) to `get_memory_by_query`. After getting Qdrant results, filter to `similarity >= min_similarity` when provided.
- [ ] **3.2** Add `async def update_memory_supersede(memory_id, new_content, user_id, collection_name, db, conversation_id=None, ...)`: load memory by id + user_id; create new memory (new content, new embedding, new row + new Qdrant point); set old row `superseded_by_id = new_memory.id`; delete old Qdrant point (or mark so it is never returned). Add `db_update_memory_superseded_by` call.
- [ ] **3.3** In [backend/app/services/qdrant_service.py](backend/app/services/qdrant_service.py): ensure you can delete a point by id when superseding (you already have `delete_points`). Call it from `update_memory_supersede` for the old memory’s embedding_id.

---

## Phase 4: Tools

- [ ] **4.1** In [backend/app/services/tools.py](backend/app/services/tools.py): implement **find_similar_memories(query)** – embed query, call `get_memory_by_query(..., min_similarity=0.9, limit=5)`, return formatted string with memory id, content, similarity (so LLM can decide to propose update).
- [ ] **4.2** Implement **create_memory(content, summary_long?, tags?, memory_type?, memory_category?, conversation_id?)** – build `MemoryCreate`, call existing `create_memory`, return success and memory id. Must receive optional conversation_id from chat context.
- [ ] **4.3** Implement **propose_memory_update(memory_id, new_content, reason?)** – validate memory exists and belongs to user and is not already superseded; insert row into pending_memory_updates; return pending id and message "Proposal created; user must confirm." Do not call update_memory_supersede.
- [ ] **4.4** Expose all four tools (search_memories, find_similar_memories, create_memory, propose_memory_update) as callables that take (db, user, conversation_id optional). Same pattern as existing `create_search_memories_tool`.

---

## Phase 5: Agentic loop and prompts

- [ ] **5.1** In [backend/app/services/llm_service.py](backend/app/services/llm_service.py): define four tools in the API schema (search_memories, find_similar_memories, create_memory, propose_memory_update) with strict parameters.
- [ ] **5.2** Replace the single tool-call pass with a loop: `while True`: call `client.responses.create(...)` with current `input_messages`; if response has no `function_call` items, break and return `output_text` and any collected `pending_memory_updates`; else for each function_call, invoke the corresponding tool, append function_call + function_call_output to `input_messages`, repeat. Cap at max 5 rounds.
- [ ] **5.3** Extend `_build_chat_prompt()`: (1) When user states a durable fact/preference/correction, first call find_similar_memories with the fact-like part of the message; (2) If no similar memory or no contradiction, call create_memory; (3) If similar and contradicting, call propose_memory_update; (4) Use search_memories for recall when answering; (5) Use focused queries per tool (fact part for find_similar/create/propose, topic for search_memories).
- [ ] **5.4** When propose_memory_update is called, collect the pending update id and metadata (memory_id, old_content, new_content, reason) so the chat response can include `pending_memory_updates`.

---

## Phase 6: Router and response shape

- [ ] **6.1** In [backend/app/routers/chatRoutes.py](backend/app/routers/chatRoutes.py): ensure `chat_service` is called with `conversation_id` (from request). Change return type so the endpoint returns JSON with both `response` (string) and `pending_memory_updates` (list of { id, memory_id, old_content, new_content, reason } when present).

---

## Phase 7: Frontend (confirm/cancel UI)

- [ ] **7.1** In [frontend/src/pages/ChatPage.jsx](frontend/src/pages/ChatPage.jsx): when the chat API response includes `pending_memory_updates`, render a confirmation block for each (e.g. below the assistant message): show old vs new content and buttons [Confirm] [Cancel].
- [ ] **7.2** On Confirm: call `POST /api/chat/memory-updates/apply` with the pending update id (or required payload). On success, remove the pending UI and optionally show a toast or refresh memories.
- [ ] **7.3** On Cancel: call cancel endpoint or simply remove the pending UI (and optionally call cancel to delete the pending row server-side).

---

## Phase 8: Testing and tuning

- [ ] **8.1** Manual test: send a message that creates a memory (e.g. "I work in Pune"). Then send "I'm in Riverside now for my masters" – expect propose_memory_update to be called and pending_memory_updates in the response; confirm UI appears.
- [ ] **8.2** Click Confirm; verify the memory is updated and the old one is archived (superseded_by_id set). Verify search_memories and find_similar_memories do not return the superseded memory.
- [ ] **8.3** Adjust model instructions if it over-creates memories or never proposes updates when it should.

---

## Optional later

- [ ] **SSE:** Stream progress events (tool_call, tool_result) during the agentic loop and send final event with reply + pending_memory_updates. Frontend consumes stream and shows "Searching memories..." then reply and confirm UI.
- [ ] **Summarize:** Keep existing Summarize flow as-is; agentic create/update is for normal chat turns only.

---

## File reference

| Phase | Main files |
|-------|------------|
| 1–2 | db_models.py, db_service.py, migration |
| 3 | memory_service.py, qdrant_service.py |
| 4 | tools.py |
| 5 | llm_service.py |
| 6 | chatRoutes.py |
| 7 | ChatPage.jsx |
| 8 | Manual testing |
