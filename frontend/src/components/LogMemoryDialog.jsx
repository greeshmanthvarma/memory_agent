import {GlassDialog, GlassDialogContent, GlassDialogHeader, GlassDialogTitle, GlassDialogFooter} from "@/components/ui/glass-dialog"
import { Textarea } from "@/components/ui/textarea"
import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"

export default function LogMemoryDialog({ open, onOpenChange }) {
    const [memory, setMemory] = useState("")
    const [isLoading, setIsLoading] = useState(false)

    async function handleSaveMemory(){
        if(!memory.trim()) {
            toast.error('Please enter a memory')
            return
        }

        setIsLoading(true)
        try{
            const response = await fetch('/api/memory/create',{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: memory.trim(),
                    memory_type: 'explicit',
                    tags: []
                }),
                credentials: 'include',
            })
            if(response.ok){
                const data = await response.json()
                if(data.is_duplicate){
                    if(data.duplicate_type === 'exact'){
                        toast.info('Memory already exists (exact match found)')
                    } else {
                        toast.info('Similar memory already exists')
                    }
                } else {
                    toast.success('Memory saved successfully')
                }
                setMemory("")
                onOpenChange(false)
            }else{
                const errorData = await response.json().catch(() => ({}))
                toast.error(errorData.detail || 'Failed to save memory')
            }
        }catch(error){
            toast.error('Failed to save memory')
        }finally{
            setIsLoading(false)
        }
    }

    const handleClose = () => {
        setMemory("")
        onOpenChange(false)
    }

    return (
        <GlassDialog open={open} onOpenChange={onOpenChange}>
            <GlassDialogContent>
                <GlassDialogHeader>
                    <GlassDialogTitle>Log Memory</GlassDialogTitle>
                </GlassDialogHeader>
                <div className="flex flex-col gap-4 py-4">
                    <Textarea 
                        placeholder="Describe your memory..." 
                        value={memory} 
                        onChange={(e) => setMemory(e.target.value)}
                        className="min-h-[120px]"
                    />
                </div>
                <GlassDialogFooter>
                    <Button variant="outline" onClick={handleClose} disabled={isLoading} className="cursor-pointer">
                        Cancel
                    </Button>
                    <Button onClick={handleSaveMemory} disabled={isLoading || !memory.trim()} className="cursor-pointer">
                        {isLoading ? 'Saving...' : 'Save Memory'}
                    </Button>
                </GlassDialogFooter>
            </GlassDialogContent>
        </GlassDialog>
    )
}