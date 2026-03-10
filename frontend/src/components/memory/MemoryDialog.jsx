import { GlassDialog, GlassDialogContent, GlassDialogHeader, GlassDialogTitle, GlassDialogDescription } from "@/components/ui/glass-dialog"
import { Button } from "@/components/ui/button"
import { useNavigate } from "react-router-dom"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { AlertDialogDestructive } from "@/components/AlertDialog"

export default function MemoryDialog({ open, onOpenChange, memory, fetchMemories }) {
    const navigate = useNavigate()
    const [isEditing, setIsEditing] = useState(false)
    const [summaryLong, setSummaryLong] = useState(memory?.summary_long ?? '')
    const [memoryContent, setMemoryContent] = useState(memory?.content ?? '')
    const [deleteMemoryOpen, setDeleteMemoryOpen] = useState(false)
    useEffect(() => {
        setIsEditing(false)
        if (memory) {   
            setSummaryLong(memory.summary_long ?? '')
            setMemoryContent(memory.content ?? '')
        }
    }, [memory, open])

    if (!memory) return null

    const formatDate = (dateString) => {
        if (!dateString) return null
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }
    async function handleSaveChanges(){
        try{
            const response = await fetch(`/api/memory/${memory.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    summary_long: summaryLong,
                    content: memoryContent
                }),
                credentials: 'include'
            })
            if (!response.ok){
                throw new Error('Failed to save changes')
            }
            const data = await response.json()
            console.log(data)
            toast.success('Changes saved successfully')
            setIsEditing(false)
            fetchMemories()
            onOpenChange(false)
        } catch (error) {
            toast.error('Failed to save changes')
        }
    }
    async function handleDelete(memoryId){
        try{
            const response = await fetch(`/api/memory/${memoryId}`, {
                method: 'DELETE',
                credentials: 'include'
            })
            if (!response.ok){
                throw new Error('Failed to delete memory')
            }
            toast.success('Memory deleted successfully')
            fetchMemories()
            onOpenChange(false)
        } catch (error) {
            toast.error('Failed to delete memory')
        }
    }    

    return (
        <GlassDialog open={open} onOpenChange={onOpenChange}>
            <GlassDialogContent className="max-w-2xl">
                <GlassDialogHeader>
                    <GlassDialogTitle className="text-lg">
                        {isEditing ? <Input value={memoryContent} onChange={(e)=>setMemoryContent(e.target.value)} /> : memory.content}
                    </GlassDialogTitle>
                    <GlassDialogDescription className="sr-only">
                        Memory details including summary, type, tags, and creation date
                    </GlassDialogDescription>
                </GlassDialogHeader>
                <div className="flex flex-col gap-4 py-4">
                    {memory.summary_long && (
                        <div className="border-b">
                            <h4 className="text-sm font-semibold mb-2 text-muted-foreground">Summary</h4>
                            {isEditing ? (
                                <Textarea className="w-full" value={summaryLong} onChange={(e)=>setSummaryLong(e.target.value)} />
                            ) : (
                                <p className="text-sm leading-relaxed pb-8">{memory.summary_long}</p>
                            )}
                        </div>
                    )}
                    
                    <div className="flex flex-wrap items-center gap-3">
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">Type:</span>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                                memory.memory_type === 'explicit' 
                                    ? 'bg-primary/20 text-primary' 
                                    : 'bg-secondary/20 text-secondary-foreground'
                            }`}>
                                {memory.memory_type === 'explicit' ? 'Explicit' : 'Implicit'}
                            </span>
                        </div>
                        
                        {memory.tags && memory.tags.length > 0 && (
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">Tags:</span>
                                <div className="flex flex-wrap gap-1">
                                    {memory.tags.map((tag, idx) => (
                                        <span key={idx} className="text-xs px-2 py-1 rounded border border-border bg-muted/50">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                        
                        {memory.created_at && (
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">Created:</span>
                                <span className="text-xs">{formatDate(memory.created_at)}</span>
                            </div>
                        )}
                        
                        {
                        memory.memory_type === 'implicit' && !memory.conversation_id ? (
                            <p className="text-xs text-muted-foreground">Conversation deleted</p>
                        ):(
                        memory.conversation_id && (
                            <Button
                                variant="link"
                                className="text-xs h-auto p-0 cursor-pointer"
                                onClick={() => {
                                    navigate(`/app/chat/${memory.conversation_id}`)
                                    onOpenChange(false)
                                }}
                            >
                                View Conversation
                            </Button>
                        ))}
                        <div className="flex items-center gap-2">
                            {!isEditing ? (
                                <Button className="cursor-pointer" onClick={()=>setIsEditing(true)}>Edit</Button> 
                            ) : (
                                <Button className="cursor-pointer" onClick={()=>handleSaveChanges()}>Save Changes</Button>
                            )}
                            <Button variant="destructive" className="cursor-pointer" onClick={()=>setDeleteMemoryOpen(true)}>Delete</Button>
                        </div>
                    </div>
                </div>
            </GlassDialogContent>
            <AlertDialogDestructive open={deleteMemoryOpen} onOpenChange={setDeleteMemoryOpen} onDelete={handleDelete} itemId={memory.id} isDeleting={false} itemType="memory" />
        </GlassDialog>
        
    )
}