import { Badge } from "@/components/ui/badge"
import type { Memory } from "@/types"

interface MemoryListProps {
  memories: Memory[]
  onMemoryClick: (memory: Memory) => void
}

function getRelativeDate(dateString: string | null): string | null {
  if (!dateString) return null
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) return 'just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 604800)}w ago`
  return `${Math.floor(diffInSeconds / 2592000)}mo ago`
}

export default function MemoryList({ memories, onMemoryClick }: MemoryListProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 mt-6">
      {memories.map(memory => (
        <div
          key={memory.id}
          onClick={() => onMemoryClick(memory)}
          className="flex flex-col cursor-pointer bg-white/10 dark:bg-gray-800/30 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-lg p-4 hover:bg-white/20 dark:hover:bg-gray-800/40 transition-colors shadow-[0_1px_1px_rgba(0,0,0,0.05),0_4px_6px_rgba(34,42,53,0.04),0_24px_68px_rgba(47,48,55,0.05),0_2px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_1px_1px_rgba(255,255,255,0.03),0_4px_6px_rgba(255,255,255,0.02),0_24px_68px_rgba(255,255,255,0.04),0_2px_3px_rgba(255,255,255,0.02)]"
        >
          <p className="text-sm text-center line-clamp-2 flex-1 mb-2">{memory.content}</p>
          <div className="flex items-center justify-between gap-2 pt-2 border-t border-gray-200 dark:border-white/15">
            <Badge variant={memory.memory_type === 'explicit' ? 'default' : 'secondary'} className="text-[10px] h-4 px-1.5">
              {memory.memory_type === 'explicit' ? 'Explicit' : 'Implicit'}
            </Badge>
            {memory.created_at && (
              <span className="text-[10px] text-muted-foreground">{getRelativeDate(memory.created_at)}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
