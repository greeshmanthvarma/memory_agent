export type MemoryType = "implicit" | "explicit" | "photo" | "calendar"
export type MemoryCategory = "fact" | "preference" | "event"
export type MutationAction = "create" | "update" | "merge" | "none"

export interface Memory {
  id: number
  content: string
  summary_long: string | null
  embedding_id: string
  memory_type: MemoryType
  memory_category: MemoryCategory | null
  conversation_id: number | null
  user_id: number
  importance_score: number
  tags: string[]
  superseded_by_id: number | null
  related_memories: number[] | null
  last_accessed_at: string | null
  last_updated_at: string | null
  created_at: string
  updated_at: string
}

export interface Conversation {
  id: number
  title: string | null
}

export interface Message {
  id: number
  content: string
  role: "user" | "assistant"
  conversation_id: number
}

export interface User {
  id: number
  username: string
  email: string
  profile_picture: string | null
}

export interface MutationQueueItem {
  created_at: string
  status: "done" | "failed" | "pending" | "processing"
  payload: {
    action: MutationAction
    memory_content: string
    target_memory_ids: number[]
    conversation_id?: number | null
    tags?: string[]
    memory_category?: MemoryCategory
  }
}

export interface ApiError {
  detail: string | Array<{ msg: string }>
}

export interface CreateMemoryResponse {
  memory: Memory
  is_duplicate: boolean
  duplicate_type: "exact" | "semantic" | null
}
