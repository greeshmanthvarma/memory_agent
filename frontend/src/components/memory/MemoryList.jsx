export default function MemoryList({ memories }) {
    return (
        <div className="space-y-4 mt-4">
            {memories.map(memory=>(
                <div key={memory.id} className="bg-white/10 cursor-pointer dark:bg-gray-800/30 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-lg p-4 shadow-md">
                    <h3 className="text-lg font-bold">{memory.content}</h3>
                </div>
            ))}
        </div>
    )
}