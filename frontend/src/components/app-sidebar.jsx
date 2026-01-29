import { Settings, SquarePen, Bubbles, ChevronDown, BrainCog, NotebookPen, User2, ChevronUp, LogOut,CircleUserRound} from "lucide-react"
import { useState,useEffect } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
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
import LogMemoryDialog from '@/components/LogMemoryDialog'
import { toast } from "sonner"

export default function AppSidebar() {
  const { state, conversations } = useSidebar()
  const { user,setUser } = useAuth()
  const [memoriesOpen, setMemoriesOpen] = useState(true)
  const [logMemoryOpen, setLogMemoryOpen] = useState(false)
  const navigate = useNavigate()
  async function handleSignOut(){
    try{
      const response = await fetch('/api/auth/logout',{
        method: 'POST',
        credentials:'include'
      })
      if(response.ok){
        setUser(null)
        toast.success('Signed out successfully')
        navigate('/login')
      }else{
        toast.error('Failed to sign out')
      }
    }catch(error){
      toast.error('Failed to sign out: ' + error.message)
    }
  }
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className={`flex-row items-center p-4 ${state === "expanded" ? "justify-between" : "justify-center"}`}>
        {state === "expanded" && (
          <p className="text-2xl font-bold">
            <Link to="/">
              Coherence
            </Link>
          </p>
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
              {state === "expanded" ? (
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
                        <SidebarMenuSubButton onClick={() => setLogMemoryOpen(true)}>
                          <NotebookPen/>
                          <span>Log Memory</span>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>
              ):(
                <SidebarMenuItem>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <SidebarMenuButton tooltip="Memories">
                        <Bubbles />
                      </SidebarMenuButton>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                      side="top"
                      className="w-[--radix-popper-anchor-width]"
                    >
                      <DropdownMenuItem asChild>
                        <Link to="/memories" className="cursor-pointer">
                          <BrainCog className="mr-2 h-4 w-4" />
                          <span>Memory Space</span>
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setLogMemoryOpen(true)} className="cursor-pointer">
                        <NotebookPen className="mr-2 h-4 w-4" />
                        <span>Log Memory</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </SidebarMenuItem>
              )}
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
                    <CircleUserRound/>
                    <span className="cursor-pointer">Account</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleSignOut} className="cursor-pointer">
                    <LogOut />
                    <span className="cursor-pointer">Sign out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      <SidebarRail />
      <LogMemoryDialog open={logMemoryOpen} onOpenChange={setLogMemoryOpen} />
    </Sidebar>
  )
}