import {InputGroup,InputGroupButton,InputGroupTextarea,InputGroupAddon} from "@/components/ui/input-group"
import { ArrowUp, Sun, Moon } from "lucide-react"
import { useTheme } from '@/ThemeContext'
import { useState,useEffect } from 'react'
import { useAuth } from '@/AuthContext'
import { useParams } from 'react-router-dom'
import {Toaster} from "@/components/ui/sonner"
import {toast} from "sonner"

export default function ChatPage() {
  return (
    <>
      <Toaster />
      <ChatPageContent />
    </>
  )
}

function ChatPageContent() {
  const { theme, toggleTheme } = useTheme()
  const [conversation,setConversation]=useState([])
  const [messages,setMessages]=useState([])
  const [error,setError]=useState(null)
  const { user } = useAuth()
  const { conversationId } = useParams()
  
  useEffect(()=>{
    async function initializeConversation(){
    if(user){
      if(conversationId){
        await fetchConversation(conversationId)
        await fetchMessages(conversationId)
        }
        else{
          await createConversation()
        }
      }else{
        setError('Please login to continue')
      }
    }
    initializeConversation()
  },[user,conversationId])
  
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
      }
      else{
        throw new Error('Failed to create conversation')
      }
    }
      catch(error){
        console.error('Error creating conversation:', error)
        setError('Failed to create conversation')
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
      <div className="flex-1 overflow-y-auto">
        {messages.map((message)=>(
          <div key={message.id} className="flex flex-col p-4 border-b border-gray-200 dark:border-gray-800">
            <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className="text-base">{message.content}</div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="w-full flex p-4">
        <div className="w-full mb-4 max-w-2xl mx-auto items-center">
          <InputGroup>
            <InputGroupTextarea 
              placeholder="Ask Away!" 
              className="overflow-y-auto max-h-[200px] min-h-[44px]"
            />
            <InputGroupAddon align="inline-end">
              <InputGroupButton variant="transparent" className="cursor-pointer hover:bg-transparent hover:text-primary">
                <ArrowUp/>
              </InputGroupButton>
            </InputGroupAddon>
          </InputGroup>
        </div>
      </div>
    </div>
  )
}
