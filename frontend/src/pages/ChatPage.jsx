import {InputGroup,InputGroupButton,InputGroupTextarea,InputGroupAddon} from "@/components/ui/input-group"
import { ArrowUp, Sun, Moon } from "lucide-react"
import { useTheme } from '@/ThemeContext'
import { useState,useEffect } from 'react'
import { useAuth } from '@/AuthContext'
import { useParams, useNavigate } from 'react-router-dom'
import {toast} from "sonner"


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
      <div className="flex-1 overflow-y-auto mx-24 my-12">
        {awaitingResponse && (
          <div className="flex justify-center items-center mb-4">
            <div className="animate-pulse w-8 h-8 bg-primary/10 rounded-full"></div>
          </div>
        )}
        {messages.map((message)=>(
          <div key={message.id} className={`flex w-fit p-4 rounded-full ${message.role === 'user' ? 'bg-primary/10' : 'none'} mb-4 ${message.role === 'user' ? 'justify-self-end' : 'justify-self-start'}`}>
            <div className="text-base">{message.content}</div>
          </div>
        ))}
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
