import { Settings, SquarePen, Bubbles, ChevronDown, BrainCog, NotebookPen, User2, ChevronUp} from "lucide-react"
import { useState,useEffect } from "react"
import { Link, useLocation } from "react-router-dom"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarTrigger,
  SidebarRail,
  useSidebar,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  SidebarFooter,
} from "@/components/ui/sidebar"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { useAuth } from '@/AuthContext'

export default function AppSidebar() {
  const { state } = useSidebar()
  const { user,loading,setUser } = useAuth()
  const [conversations,setConversations]=useState([])
  const [memoriesOpen, setMemoriesOpen] = useState(true)

  useEffect(()=>{
    async function fetchConversations(){
      if(!user || loading) return
      try{
        const response=await fetch('/api/chat/conversation/all',{
          credentials:'include'
        })
        if(response.ok){
          const data=await response.json()
          setConversations(data.conversations || [])
        }else{
          const errorData = await response.json().catch(() => ({}))
          console.error('Failed to fetch conversations:', response.status, errorData)
        }
      }catch(error){
        console.error('Error fetching conversations:', error)
      }
    }
    fetchConversations()
  },[user, loading])
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className={`flex-row items-center p-4 ${state === "expanded" ? "justify-between" : "justify-center"}`}>
        {state === "expanded" && (
          <p className="text-2xl font-bold">Coherence</p>
        )}
        <SidebarTrigger />
      </SidebarHeader>
      
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link to="/chat">
                    <SquarePen />
                    <span>
                       New Chat
                    </span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              
              <Collapsible
                asChild
                open={memoriesOpen}
                onOpenChange={setMemoriesOpen}
              >
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton tooltip="Memories" className="cursor-pointer">
                      <Bubbles />
                      <span>Memories</span>
                      <ChevronDown className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-180" />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <SidebarMenuSub>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton asChild>
                          <Link to="/memories">
                            <BrainCog/>
                            <span>Memory Space</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton asChild>
                          <a href="#">
                            <NotebookPen/>
                            <span>Log Memory</span>
                          </a>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>
              
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <a href="#">
                    <Settings />
                    <span>Settings</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {state === "expanded" && (
          <SidebarGroup>
            <SidebarGroupLabel>Your Chats</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {conversations.map((conversation)=>(
                  <SidebarMenuItem key={conversation.id}>
                    <SidebarMenuButton asChild>
                      <Link to={`/chat/${conversation.id}`}>
                        <span>{conversation.title || `Chat ${conversation.id}`}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>
      <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuButton>
                    <User2 /> {user.username}
                    <ChevronUp className="ml-auto" />
                  </SidebarMenuButton>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  side="top"
                  className="w-[--radix-popper-anchor-width]"
                >
                  <DropdownMenuItem>
                    <span>Account</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <span>Sign out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}