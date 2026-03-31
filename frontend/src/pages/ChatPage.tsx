import { InputGroup, InputGroupButton, InputGroupTextarea, InputGroupAddon } from "@/components/ui/input-group"
import { ArrowUp, Sun, Moon } from "lucide-react"
import { useTheme } from '@/ThemeContext'
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/AuthContext'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from "sonner"
import ReactMarkdown from "react-markdown"
import { Button } from '@/components/ui/button'
import { useSidebar, SidebarTrigger } from '@/components/ui/sidebar'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import ViewMemoryChangesDialog from "@/components/ViewMemoryChangesDialog"
import type { Conversation, Message, MutationQueueItem } from '@/types'

const POLL_INTERVAL_MS = 2000
const POLL_TIMEOUT_MS = 20000

interface LocalMessage {
  id: string | number
  content: string
  role: 'user' | 'assistant'
  conversation_id?: number
}

export default function ChatPage() {
  const { theme, toggleTheme } = useTheme()
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<LocalMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  const [awaitingResponse, setAwaitingResponse] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const { user } = useAuth()
  const { conversationId } = useParams<{ conversationId: string }>()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const isInitialLoadRef = useRef(false)
  const loadedConversationIdRef = useRef<string | number | null>(null)
  const streamingContentRef = useRef('')
  const isSendingMessageRef = useRef(false)
  const [isSummarizing, setIsSummarizing] = useState(false)
  const { refreshConversations } = useSidebar()
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [memoryUpdate, setMemoryUpdate] = useState<MutationQueueItem | null>(null)
  const [viewChangesDialogOpen, setViewChangesDialogOpen] = useState(false)
  const mutationPollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    async function initializeConversation() {
      if (!user) { navigate('/'); return }
      if (!conversationId) {
        setConversation(null)
        setMessages([])
        setLoadingMessages(false)
        loadedConversationIdRef.current = null
        return
      }
      if (String(loadedConversationIdRef.current) !== String(conversationId)) {
        setLoadingMessages(true)
      }
      isInitialLoadRef.current = true
      await fetchConversation(conversationId)
      const messagesData = await fetchMessages(conversationId)
      if (!isSendingMessageRef.current && messagesData != null) {
        setMessages(messagesData)
      }
      loadedConversationIdRef.current = conversationId
      setLoadingMessages(false)
    }
    initializeConversation()
  }, [user, conversationId])

  useEffect(() => {
    if (error) { toast.error(error); setError(null) }
  }, [error])

  useEffect(() => {
    if (messagesEndRef.current && messagesContainerRef.current) {
      const container = messagesContainerRef.current
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      if (isInitialLoadRef.current || messages.length === 0) {
        setTimeout(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'auto' }) }, 100)
        isInitialLoadRef.current = false
      } else if (isNearBottom) {
        setTimeout(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, 100)
      }
    }
  }, [messages])

  useEffect(() => {
    return () => {
      if (mutationPollIntervalRef.current) clearInterval(mutationPollIntervalRef.current)
    }
  }, [])

  async function fetchConversation(id: string) {
    try {
      const response = await fetch(`/api/chat/conversation/${id}`, { credentials: 'include' })
      if (response.ok) {
        const data: { conversation: Conversation } = await response.json()
        setConversation(data.conversation)
      } else {
        throw new Error('Failed to fetch conversation')
      }
    } catch (error) {
      console.error('Error fetching conversation:', error)
      setError('Failed to fetch conversation')
    }
  }

  async function fetchMessages(id: string): Promise<LocalMessage[] | null> {
    try {
      const response = await fetch(`/api/chat/conversation/${id}/messages`, { credentials: 'include' })
      if (response.ok) {
        const data: { messages: Message[] } = await response.json()
        return data.messages
      } else {
        throw new Error('Failed to fetch messages')
      }
    } catch {
      setLoadingMessages(false)
      toast.error('Failed to fetch messages')
      return null
    }
  }

  async function createConversation(): Promise<number | null> {
    try {
      const response = await fetch('/api/chat/conversation', { method: 'POST', credentials: 'include' })
      if (response.ok) {
        const data: { conversation: Conversation } = await response.json()
        setConversation(data.conversation)
        return data.conversation.id
      } else {
        throw new Error('Failed to create conversation')
      }
    } catch (error) {
      console.error('Error creating conversation:', error)
      setError('Failed to create conversation')
      return null
    }
  }

  async function updateConversationTitle(id: number, message: string): Promise<string | null> {
    try {
      const response = await fetch(`/api/chat/conversation/${id}/title`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ first_message: message })
      })
      if (response.ok) {
        const data: { title: string } = await response.json()
        refreshConversations()
        return data.title
      } else {
        throw new Error('Failed to update conversation title')
      }
    } catch (error) {
      console.error('Error updating conversation title:', error)
      setError('Failed to update conversation title')
      return null
    }
  }

  async function pollForMemoryUpdates(): Promise<MutationQueueItem | null> {
    try {
      const response = await fetch('/api/memory/mutation-queue', { credentials: 'include' })
      if (response.ok) return await response.json()
      throw new Error('Failed to poll for memory updates')
    } catch (error) {
      console.error('Error polling for memory updates:', error)
      toast.error('Failed to poll for memory updates')
      return null
    }
  }

  function pollForMemoryUpdateUntilTerminal(sentAt: number) {
    let elapsedMs = 0
    let isPolling = false
    if (mutationPollIntervalRef.current) clearInterval(mutationPollIntervalRef.current)

    const intervalId = setInterval(async () => {
      if (isPolling) return
      isPolling = true
      try {
        const update = await pollForMemoryUpdates()
        elapsedMs += POLL_INTERVAL_MS
        const jobCreatedMs = update?.created_at ? new Date(update.created_at).getTime() : NaN
        if (!update || Number.isNaN(jobCreatedMs) || jobCreatedMs < sentAt) {
          if (elapsedMs > POLL_TIMEOUT_MS) { clearInterval(intervalId); mutationPollIntervalRef.current = null }
          return
        }
        const status = update.status
        const isTerminal = status === 'done' || status === 'failed'
        const isTimedOut = elapsedMs > POLL_TIMEOUT_MS
        if (isTerminal || isTimedOut) {
          if (status === 'done') {
            toast(
              <div className="flex flex-col gap-2">
                <p>Memory updated successfully</p>
                <button className="underline" onClick={() => setViewChangesDialogOpen(true)}>View Changes</button>
              </div>
            )
            setMemoryUpdate(update)
          } else if (status === 'failed') {
            toast.error('Failed to apply memory update')
          }
          clearInterval(intervalId)
          mutationPollIntervalRef.current = null
        }
      } catch (err) {
        console.error('Error polling memory updates interval:', err)
        toast.error('Error while checking memory updates')
        clearInterval(intervalId)
        mutationPollIntervalRef.current = null
      } finally {
        isPolling = false
      }
    }, POLL_INTERVAL_MS)

    mutationPollIntervalRef.current = intervalId
  }

  async function handleSendMessage() {
    if (!inputValue.trim()) return
    const message = inputValue.trim()
    let currentConversationId: number | string | null = conversationId || conversation?.id || null

    if (!currentConversationId) {
      currentConversationId = await createConversation()
      if (!currentConversationId) { setError('Failed to create conversation'); return }
      updateConversationTitle(currentConversationId as number, message)
      loadedConversationIdRef.current = currentConversationId
      isSendingMessageRef.current = true
      navigate(`/app/chat/${currentConversationId}`, { replace: true })
      refreshConversations()
    }

    setInputValue('')
    const optimisticId = `temp-${Date.now()}`
    const optimisticUserMessage: LocalMessage = { content: message, role: 'user', id: optimisticId }
    setMessages(prev => [...prev, optimisticUserMessage])
    setAwaitingResponse(true)
    const sentAt = Date.now()

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_message: message, conversation_id: currentConversationId })
      })
      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}))
        throw new Error((errBody as { detail?: string }).detail || `${response.status} ${response.statusText}`)
      }
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      const streamingId = `streaming-${Date.now()}`
      streamingContentRef.current = ''
      let firstChunk = true

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = value ? decoder.decode(value, { stream: true }) : ''
        if (!text) continue
        streamingContentRef.current += text
        if (firstChunk) {
          setMessages(prev => [...prev, { content: streamingContentRef.current, role: 'assistant', id: streamingId }])
          setAwaitingResponse(false)
          firstChunk = false
        } else {
          setMessages(prev => prev.map(m => m.id === streamingId ? { ...m, content: streamingContentRef.current } : m))
        }
      }

      pollForMemoryUpdateUntilTerminal(sentAt)
    } catch (error) {
      console.error('Error sending message:', error)
      const displayMsg = error instanceof Error ? error.message : 'Failed to send message'
      setError(displayMsg)
      toast.error(displayMsg)
      setMessages(prev => prev.filter(msg => msg.id !== optimisticId))
      setAwaitingResponse(false)
    } finally {
      isSendingMessageRef.current = false
    }
  }

  async function onSummarizeConversation() {
    setIsSummarizing(true)
    try {
      const response = await fetch('/api/chat/conversation/summarize', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId, messages })
      })
      if (response.ok) {
        const data: { message: string } = await response.json()
        if (data.message === 'Memory created successfully') {
          toast.success('Memory created successfully')
        } else {
          toast.error(data.message)
        }
      } else {
        toast.error('Failed to summarize conversation')
        throw new Error('Failed to summarize conversation')
      }
    } catch (error) {
      console.error('Error summarizing conversation:', error)
      toast.error('Failed to summarize conversation')
    } finally {
      setIsSummarizing(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="sticky top-0 z-10 flex justify-between items-center px-4 py-2 border-b border-border/40">
        <div className="flex items-center gap-2">
          <div className="md:hidden shrink-0">
            <SidebarTrigger />
          </div>
          {conversationId && messages.length > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={onSummarizeConversation}
                  variant="outline"
                  size="sm"
                  className="cursor-pointer text-xs h-8"
                  disabled={isSummarizing}
                >
                  {isSummarizing ? 'Summarizing...' : 'Summarize Conversation'}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-xs text-muted-foreground">Extract and save to memory</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
        <button
          onClick={toggleTheme}
          className="p-2 rounded-full cursor-pointer bg-white/30 dark:bg-gray-900/50 backdrop-blur-xl border border-white/30 dark:border-white/10 hover:bg-white/40 dark:hover:bg-gray-900/60 transition-all"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5 text-black dark:text-white" /> : <Moon className="w-5 h-5 text-black dark:text-white" />}
        </button>
      </div>

      <div
        ref={messagesContainerRef}
        className={`flex-1 overflow-y-auto px-4 py-8 ${messages.length === 0 && !conversationId && !isSummarizing ? 'flex items-center justify-center' : ''}`}
      >
        {messages.length === 0 && !conversationId && !isSummarizing ? (
          <div className="text-center text-3xl text-muted-foreground">Hello! Good to see you here.</div>
        ) : loadingMessages ? (
          <div className="flex items-center justify-center h-64">
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-muted-foreground">Loading messages...</p>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`px-4 py-3 rounded-2xl ${message.role === 'user' ? 'max-w-[80%] bg-primary/10 text-foreground' : 'max-w-[95%] text-foreground'}`}>
                  {message.role === 'user' ? (
                    <div className="text-base whitespace-pre-wrap break-words">{message.content}</div>
                  ) : (
                    <div className="text-base break-words [&_p]:mb-2 [&_p:last-child]:mb-0 [&_strong]:font-semibold [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_pre]:bg-muted [&_pre]:p-4 [&_pre]:rounded-lg [&_pre]:overflow-x-auto [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_ul]:list-disc [&_ul]:ml-4 [&_ol]:list-decimal [&_ol]:ml-4 [&_li]:mb-1">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {awaitingResponse && (
              <div className="flex justify-start">
                <div className="px-4 py-3 rounded-2xl max-w-[95%] text-foreground bg-muted/50">
                  <span className="inline-flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="w-full flex p-4">
        <div className="w-full mb-4 max-w-2xl mx-auto items-center">
          <InputGroup>
            <InputGroupTextarea
              placeholder="Ask Away!"
              className="overflow-y-auto max-h-[200px] min-h-[44px]"
              value={inputValue}
              disabled={isSummarizing}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
            />
            <InputGroupAddon align="inline-end">
              <InputGroupButton
                variant="ghost"
                className="cursor-pointer hover:bg-transparent hover:text-primary"
                onClick={handleSendMessage}
                disabled={isSummarizing}
              >
                <ArrowUp />
              </InputGroupButton>
            </InputGroupAddon>
          </InputGroup>
        </div>
      </div>
      <ViewMemoryChangesDialog open={viewChangesDialogOpen} onOpenChange={setViewChangesDialogOpen} memoryUpdate={memoryUpdate} />
    </div>
  )
}
