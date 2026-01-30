
export default function MemoryList({ memories, onMemoryClick }) {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 mt-4">
            {memories.map(memory=>(
                <div key={memory.id} onClick={()=>onMemoryClick(memory)} className="flex items-center justify-center cursor-pointer bg-white/10 dark:bg-gray-800/30 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-lg p-4 shadow-md">
                    <p className="text-sm text-center line-clamp-2">{memory.content}</p>
                </div>
            ))}
        </div>
    )
}