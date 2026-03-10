import { Settings, SquarePen, Bubbles, ChevronDown, BrainCog, NotebookPen, User2, ChevronUp, LogOut,UserRoundPen,Ellipsis,Pencil,Trash2} from "lucide-react"
import { useState,useEffect, useRef } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
import EditProfileDialog from "@/components/EditProfileDialog"
import { AlertDialogDestructive } from "@/components/AlertDialog"

export default function AppSidebar() {
  const { state, conversations, refreshConversations } = useSidebar()
  const { user,setUser } = useAuth()
  const location = useLocation()
  const [memoriesOpen, setMemoriesOpen] = useState(true)
  const [logMemoryOpen, setLogMemoryOpen] = useState(false)
  const [editProfileOpen, setEditProfileOpen] = useState(false)
  const [hoveredConversationId, setHoveredConversationId] = useState(null)
  const [editingConversationId, setEditingConversationId] = useState(null)
  const [deleteConversationOpen, setDeleteConversationOpen] = useState(false)
  const [deleteConversationId, setDeleteConversationId] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [editingConversationTitle, setEditingConversationTitle] = useState('')
  const [isUpdatingTitle, setIsUpdatingTitle] = useState(false)
  const titleInputRef = useRef(null)
  const navigate = useNavigate()
  
  const currentConversationId = location.pathname.startsWith('/app/chat/') 
    ? parseInt(location.pathname.split('/app/chat/')[1]) 
    : null
  async function handleSignOut(){
    try{
      const response = await fetch('/api/auth/logout',{
        method: 'POST',
        credentials:'include'
      })
      if(response.ok){
        setUser(null)
        toast.success('Signed out successfully')
        navigate('/')
      }else{
        toast.error('Failed to sign out')
      }
    }catch(error){
      toast.error('Failed to sign out: ' + error.message)
    }
  }

  async function handleDeleteConversation(conversationId) {
    if (!conversationId) return
    setIsDeleting(true)

    try {
      const response = await fetch(`/api/chat/conversation/${conversationId}`, {
        method: 'DELETE',
        credentials: 'include'
      })

      if (response.ok) {
        toast.success('Conversation deleted successfully')
        setDeleteConversationOpen(false)
        setDeleteConversationId(null)
        setIsDeleting(false)
        await refreshConversations()
        
        if (currentConversationId === conversationId) {
          navigate('/app/chat')
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        toast.error(errorData.detail || 'Failed to delete conversation')
        setIsDeleting(false)
      }
    } catch (error) {
      toast.error('Failed to delete conversation: ' + error.message)
      setIsDeleting(false)
    }
  }

  async function editConversationTitle(conversationId, title) {
    if (!title || !title.trim()) {
      toast.error('Title cannot be empty')
      return
    }
    
    setIsUpdatingTitle(true)
    try {
      const response = await fetch(`/api/chat/conversation/${conversationId}`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: title.trim() })
      })
      if (response.ok) {
        toast.success('Conversation title updated successfully')
        setEditingConversationId(null)
        setEditingConversationTitle('')
        await refreshConversations()
      } else {
        const errorData = await response.json().catch(() => ({}))
        toast.error(errorData.detail || 'Failed to update conversation title')
      }
    } catch (error) {
      toast.error('Failed to update conversation title: ' + error.message)
    } finally {
      setIsUpdatingTitle(false)
    }
  }

  function handleStartEdit(conversation) {
    setEditingConversationId(conversation.id)
    setEditingConversationTitle(conversation.title || `Chat ${conversation.id}`)
    setTimeout(() => {
      if (titleInputRef.current) {
        titleInputRef.current.focus() //focus the input
        titleInputRef.current.select() //select the text in the input
      }
    }, 0)
  }

  function handleCancelEdit() {
    setEditingConversationId(null)
    setEditingConversationTitle('')
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
                  <Link to="/app/chat">
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
                          <Link to="/app/memories">
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
                      side="right"
                      align="end"
                      className="w-[--radix-popper-anchor-width]"
                    >
                      <DropdownMenuItem asChild>
                        <Link to="/app/memories" className="cursor-pointer">
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
                    <div 
                      id={`conversation-${conversation.id}`}
                      className={`flex items-center justify-between rounded-md gap-2 group ${currentConversationId === conversation.id ? "bg-sidebar-accent text-sidebar-accent-foreground" : ""}`}
                      onMouseEnter={() => setHoveredConversationId(conversation.id)}
                      onMouseLeave={() => {
                        if (!document.querySelector(`[data-state="open"]`)) {
                          setHoveredConversationId(null)
                        }
                      }}
                    >
                      {editingConversationId === conversation.id ? (
                        <Input 
                          ref={titleInputRef}
                          type="text" 
                          value={editingConversationTitle} 
                          onChange={(e) => setEditingConversationTitle(e.target.value)} 
                          onBlur={() => {
                            if (editingConversationTitle.trim() && editingConversationTitle !== (conversation.title || '' || `Chat ${conversation.id}`)) {
                              editConversationTitle(conversation.id, editingConversationTitle)
                            } else {
                              handleCancelEdit()
                            }
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault()
                              if (editingConversationTitle.trim()) {
                                editConversationTitle(conversation.id, editingConversationTitle)
                              }
                            } else if (e.key === 'Escape') {
                              e.preventDefault()
                              handleCancelEdit()
                            }
                          }}
                          disabled={isUpdatingTitle}
                          className="flex-1"
                          placeholder="Enter title..."
                        />
                      ) : (
                        <SidebarMenuButton asChild className="flex-1">
                          <Link to={`/app/chat/${conversation.id}`}>
                            <span>{conversation.title || `Chat ${conversation.id}`}</span>
                          </Link>
                        </SidebarMenuButton>
                      )}
                      {hoveredConversationId === conversation.id && (
                        <DropdownMenu 
                          onOpenChange={(open) => {
                            if (!open) {
                              setHoveredConversationId(null)
                            }
                          }}
                        >
                          <DropdownMenuTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity"
                              onMouseEnter={(e) => e.stopPropagation()}
                            >
                              <Ellipsis/>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent
                            side="right"
                            align="end"
                            className="w-48"
                            onMouseLeave={() => setHoveredConversationId(null)}
                          >
                            <DropdownMenuItem 
                              onClick={() => handleStartEdit(conversation)} 
                              className="cursor-pointer"
                            >
                              <Pencil className="mr-2 h-4 w-4"/>
                              <span>Rename</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => {
                                setDeleteConversationId(conversation.id)
                                setDeleteConversationOpen(true)
                              }} 
                              className="cursor-pointer text-destructive focus:text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              <span>Delete Conversation</span>
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
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
                    <User2 /> {user?.username ?? 'Account'}
                    <ChevronUp className="ml-auto" />
                  </SidebarMenuButton>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  side="top"
                  className="w-[--radix-popper-anchor-width]"
                >
                  <DropdownMenuItem onClick={() => setEditProfileOpen(true)} className="cursor-pointer">
                    <UserRoundPen/>
                    <span className="cursor-pointer">Edit Profile</span>
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
      <EditProfileDialog open={editProfileOpen} onOpenChange={setEditProfileOpen} />
      <AlertDialogDestructive open={deleteConversationOpen} onOpenChange={setDeleteConversationOpen} onDelete={handleDeleteConversation} itemId={deleteConversationId} isDeleting={isDeleting} itemType="conversation" />
    </Sidebar>
  )
}