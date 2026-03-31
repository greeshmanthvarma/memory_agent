import MemoryBubble from "./MemoryBubble"
import type { Memory } from "@/types"

interface MemoryBubblesGridProps {
  memories: Memory[]
  onMemoryClick: (memory: Memory) => void
}

export default function MemoryBubblesGrid({ memories, onMemoryClick }: MemoryBubblesGridProps) {
  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-2 mt-4">
      {memories.map(memory => (
        <MemoryBubble key={memory.id} memory={memory} onClick={() => onMemoryClick(memory)} />
      ))}
    </div>
  )
}
