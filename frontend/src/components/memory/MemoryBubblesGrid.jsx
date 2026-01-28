import MemoryBubble from "./MemoryBubble"

export default function MemoryBubblesGrid({ memories }) {
    return (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 mt-4">
            {memories.map(memory=>(
                <MemoryBubble key={memory.id} memory={memory} />
            ))}
        </div>
    )
}