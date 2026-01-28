import { useEffect, useState } from 'react'
import { useAuth } from '@/AuthContext'
import { toast } from 'sonner'
import MemoryBubblesGrid from '@/components/memory/MemoryBubblesGrid'
import MemoryList from '@/components/memory/MemoryList'
import { Button } from '@/components/ui/button'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/ThemeContext'
import { ArrowLeftIcon } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
export default function MemorySpacePage() {

  const [memories,setMemories]=useState([])
  const {user}=useAuth()
  const [bubbleView,setBubbleView]=useState(true)
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate()
  useEffect(()=>{
    async function fetchMemories(){
      if(!user){
        toast.error('Please login to continue')
        return
      }
      try{
        const response =await fetch('/api/memory',{
          credentials:'include',
          headers:{
            'Content-Type': 'application/json'
          }
        })
        if(response.ok){
          const data=await response.json()
          console.log(data)
          setMemories(data || [])
        }else{
          const errorData = await response.json().catch(() => ({}))
          toast.error(errorData.detail || 'Failed to fetch memories')
        }
      }catch(error){
        toast.error('Failed to fetch memories: ' + error.message)
      }
    }
    fetchMemories()
  },[user])

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center justify-center gap-2">
          <Button onClick={()=> navigate(-1)} variant="ghost" size="icon">
            <ArrowLeftIcon className="w-4 h-4" />
          </Button>
          <h1 className="text-2xl font-bold">Memory Space</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <Button onClick={()=>setBubbleView(!bubbleView)}>
            {bubbleView ? 'List View' : 'Bubble View'}
          </Button>
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
        
      </div>
      {
        bubbleView ? (
          <MemoryBubblesGrid memories={memories} />
        ) : (
          <MemoryList memories={memories} />
        )
      }
      
    </div>
  )
}
