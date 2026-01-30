import { GlassDialog, GlassDialogContent, GlassDialogHeader, GlassDialogTitle } from "@/components/ui/glass-dialog"
import { Button } from "@/components/ui/button"
import { useNavigate } from "react-router-dom"

export default function MemoryDialog({ open, onOpenChange, memory }) {
    const navigate = useNavigate()
    
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
   
    return (
        <GlassDialog open={open} onOpenChange={onOpenChange}>
            <GlassDialogContent className="max-w-2xl">
                <GlassDialogHeader>
                    <GlassDialogTitle className="text-lg">{memory.content}</GlassDialogTitle>
                </GlassDialogHeader>
                <div className="flex flex-col gap-4 py-4">
                    {memory.summary_long && (
                        <div>
                            <h4 className="text-sm font-semibold mb-2 text-muted-foreground">Summary</h4>
                            <p className="text-sm leading-relaxed">{memory.summary_long}</p>
                        </div>
                    )}
                    
                    <div className="flex flex-wrap items-center gap-3 pt-2 border-t">
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
                        
                        {memory.conversation_id && (
                            <Button
                                variant="link"
                                className="text-xs h-auto p-0 cursor-pointer"
                                onClick={() => {
                                    navigate(`/chat/${memory.conversation_id}`)
                                    onOpenChange(false)
                                }}
                            >
                                View Conversation
                            </Button>
                        )}
                    </div>
                </div>
            </GlassDialogContent>
        </GlassDialog>
    )
}