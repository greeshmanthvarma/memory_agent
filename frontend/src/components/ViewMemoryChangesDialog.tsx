import { GlassDialog, GlassDialogContent, GlassDialogHeader, GlassDialogTitle } from "@/components/ui/glass-dialog"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import type { MutationQueueItem, Memory } from "@/types"

interface ViewMemoryChangesDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  memoryUpdate: MutationQueueItem | null
}

export default function ViewMemoryChangesDialog({ open, onOpenChange, memoryUpdate }: ViewMemoryChangesDialogProps) {
  const [oldMemories, setOldMemories] = useState<Partial<Memory>[]>([])
  const [newMemories, setNewMemories] = useState<Partial<Memory>[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!memoryUpdate || !open) return
    let cancelled = false

    async function load() {
      setLoading(true)
      setOldMemories([])
      setNewMemories([])
      try {
        const payload = memoryUpdate!.payload
        const targetIds = payload?.target_memory_ids ?? []

        const oldList: Partial<Memory>[] = []
        for (const id of targetIds) {
          const res = await fetch(`/api/memory/${id}`, { credentials: 'include' })
          if (res.ok) oldList.push(await res.json())
        }
        if (cancelled) return
        setOldMemories(oldList)

        const newIds = [...new Set(oldList.map((m) => m.superseded_by_id).filter((id): id is number => id != null))]
        const newList: Partial<Memory>[] = []
        for (const id of newIds) {
          const res = await fetch(`/api/memory/${id}`, { credentials: 'include' })
          if (res.ok) newList.push(await res.json())
        }

        if (targetIds.length === 0 && payload?.memory_content) {
          newList.push({ id: undefined, content: payload.memory_content })
        }

        if (cancelled) return
        setNewMemories(newList)
      } catch (err) {
        console.error('Error fetching memories:', err)
        toast.error('Failed to load memory changes')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [memoryUpdate, open])

  return (
    <GlassDialog open={open} onOpenChange={onOpenChange}>
      <GlassDialogContent>
        <GlassDialogHeader>
          <GlassDialogTitle>Memory Change</GlassDialogTitle>
        </GlassDialogHeader>
        {loading ? (
          <p className="text-muted-foreground">Loading changes…</p>
        ) : memoryUpdate?.payload?.action === 'create' ? (
          <div className="flex flex-col gap-2">
            <h3 className="text-lg font-medium">New Memory</h3>
            <p className="text-sm text-muted-foreground">{memoryUpdate?.payload?.memory_content}</p>
          </div>
        ) : memoryUpdate?.payload?.action === 'update' || memoryUpdate?.payload?.action === 'merge' ? (
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <h3 className="text-lg font-medium">Before</h3>
              <ul className="list-disc list-inside">
                {oldMemories.map((memory, i) => (
                  <li key={memory.id ?? i}>{memory.content}</li>
                ))}
                {oldMemories.length === 0 && <li className="text-muted-foreground">—</li>}
              </ul>
            </div>
            <div className="flex flex-col gap-2">
              <h3 className="text-lg font-medium">After</h3>
              <ul className="list-disc list-inside">
                {newMemories.map((memory, i) => (
                  <li key={memory.id ?? i}>{memory.content}</li>
                ))}
                {newMemories.length === 0 && memoryUpdate?.payload?.memory_content && !loading && (
                  <li>{memoryUpdate.payload.memory_content}</li>
                )}
                {newMemories.length === 0 && !memoryUpdate?.payload?.memory_content && !loading && (
                  <li className="text-muted-foreground">—</li>
                )}
              </ul>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <h3 className="text-lg font-medium">No changes</h3>
            <p className="text-sm text-muted-foreground">No changes were made to the memory</p>
          </div>
        )}
      </GlassDialogContent>
    </GlassDialog>
  )
}
