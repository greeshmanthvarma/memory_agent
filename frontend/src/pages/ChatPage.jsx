import {InputGroup,InputGroupButton,InputGroupTextarea,InputGroupAddon} from "@/components/ui/input-group"
import { ArrowUp, Sun, Moon } from "lucide-react"
import { useTheme } from '@/ThemeContext'
import { useState,useEffect, useRef } from 'react'
import { useAuth } from '@/AuthContext'
import { useParams, useNavigate } from 'react-router-dom'
import {toast} from "sonner"
import ReactMarkdown from "react-markdown"

export default function ChatPage() {
  const { theme, toggleTheme } = useTheme()
  const [conversation,setConversation]=useState(null)
  const [messages,setMessages]=useState([])
  const [error,setError]=useState(null)
  const [awaitingResponse,setAwaitingResponse]=useState(false)
  const [inputValue, setInputValue] = useState('')
  const { user } = useAuth()
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const isInitialLoadRef = useRef(false)

  useEffect(()=>{
    async function initializeConversation(){
      if(!user){
        setError('Please login to continue')
        return
      }

      if(!conversationId){
        setConversation(null)
        setMessages([])
        return
      }

      isInitialLoadRef.current = true
      await fetchConversation(conversationId)
      await fetchMessages(conversationId)
    }
    initializeConversation()
  },[user, conversationId])
  
  useEffect(()=>{
    if(error){
      toast.error(error)
      setError(null)
    }
  },[error])

  useEffect(()=>{
    if(messagesEndRef.current && messagesContainerRef.current){
      const container = messagesContainerRef.current
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      
      if(isInitialLoadRef.current || messages.length === 0){
        setTimeout(() => {
          if(messagesEndRef.current){
            messagesEndRef.current.scrollIntoView({ behavior: 'auto' })
          }
        }, 100)
        isInitialLoadRef.current = false
      } else if(isNearBottom){
        setTimeout(() => {
          if(messagesEndRef.current){
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
          }
        }, 100)
      }
    }
  },[messages])
  
  async function fetchConversation(conversationId){
      try{
        const response=await fetch(`/api/chat/conversation/${conversationId}`,{
          credentials:'include'
        })
        if(response.ok){
          const data=await response.json()
          setConversation(data.conversation)
        }
        else{
          throw new Error('Failed to fetch conversation')
        }
      }
      catch(error){
        console.error('Error fetching conversation:', error)
        setError('Failed to fetch conversation')
      }
    }

    async function fetchMessages(conversationId){
      try{
        const response = await fetch(`/api/chat/conversation/${conversationId}/messages`,{
          credentials:'include'
        })
        if(response.ok){
          const data=await response.json()
          setMessages(data.messages)
        }
        else{
          throw new Error('Failed to fetch messages')
        }
      }
      catch(error){
        console.error('Error fetching messages:', error)
        setError('Failed to fetch messages')
      }
    }
  
    async function createConversation(){
      try{
        const response=await fetch('/api/chat/conversation',{
          method:'POST',
          credentials:'include'
        })
      
      if(response.ok){
        const data=await response.json()
        setConversation(data.conversation)
        return data.conversation.id
      }
      else{
        throw new Error('Failed to create conversation')
      }
    }
      catch(error){
        console.error('Error creating conversation:', error)
        setError('Failed to create conversation')
        return null
      }
    }

    async function handleSendMessage(){
      if(!inputValue.trim()) return
      
      let currentConversationId = conversationId || (conversation?.id)
      
      if(!currentConversationId){
        currentConversationId = await createConversation()
        if(!currentConversationId){
          setError('Failed to create conversation')
          return
        }
        navigate(`/chat/${currentConversationId}`, { replace: true })
      }

      const message = inputValue.trim()
      setInputValue('')
      
      const optimisticUserMessage = {content: message, role: 'user', id: `temp-${Date.now()}`}
      setMessages(prev => [...prev, optimisticUserMessage])
      setAwaitingResponse(true)
      try{
        const response = await fetch('/api/chat',{
          method:'POST',
          credentials:'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_message: message,
            conversation_id: currentConversationId
          })
        })
        if(response.ok){
          setAwaitingResponse(false)
          await fetchMessages(currentConversationId)
        }
        else{
          throw new Error('Failed to send message')
        }
      }
      catch(error){
        console.error('Error sending message:', error)
        setError('Failed to send message')
        setMessages(prev => prev.filter(msg => msg.id !== optimisticUserMessage.id))
        setAwaitingResponse(false)
      }
    }
  return (
  <div className="flex flex-col h-full">
      <div className='absolute top-4 right-4'>
      <button
            onClick={toggleTheme}
            className="p-2 rounded-full cursor-pointer bg-white/30 dark:bg-gray-900/50 backdrop-blur-xl border border-white/30 dark:border-white/10 hover:bg-white/40 dark:hover:bg-gray-900/60 transition-all"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-black dark:text-white" />
            ) : (
              <Moon className="w-5 h-5 text-black dark:text-white" />
            )}
          </button>
      </div>
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-4">
          
          {messages.map((message)=>(
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`px-4 py-3 rounded-2xl ${
                  message.role === 'user'
                    ? 'max-w-[80%] bg-primary/10 text-foreground'
                    : 'max-w-[95%] text-foreground'
                }`}
              >
                {
                  message.role === 'user' ? (
                    <div className="text-base whitespace-pre-wrap break-words">{message.content}</div>
                  ) :(
                    <div className="text-base break-words [&_p]:mb-2 [&_p:last-child]:mb-0 [&_strong]:font-semibold [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_pre]:bg-muted [&_pre]:p-4 [&_pre]:rounded-lg [&_pre]:overflow-x-auto [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_ul]:list-disc [&_ul]:ml-4 [&_ol]:list-decimal [&_ol]:ml-4 [&_li]:mb-1">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                    )
                }
              </div>
            </div>
          ))}
          <div ref={messagesEndRef}></div>
        </div>
      </div>
      
      <div className="w-full flex p-4">
        <div className="w-full mb-4 max-w-2xl mx-auto items-center">
          <InputGroup>
            <InputGroupTextarea 
              placeholder="Ask Away!" 
              className="overflow-y-auto max-h-[200px] min-h-[44px]"
              value={inputValue}
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
                variant="transparent" 
                className="cursor-pointer hover:bg-transparent hover:text-primary"
                onClick={handleSendMessage}
              >
                <ArrowUp/>
              </InputGroupButton>
            </InputGroupAddon>
          </InputGroup>
        </div>
      </div>
    </div>
  )
}
