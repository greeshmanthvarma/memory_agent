import { motion } from "motion/react"
import { useMemo } from "react"
import type { Memory } from "@/types"

interface MemoryBubbleProps {
  memory: Memory
  onClick: () => void
}

export default function MemoryBubble({ memory, onClick }: MemoryBubbleProps) {
  const { path, duration, rotation } = useMemo(() => {
    const radiusX = 15 + Math.random() * 20
    const radiusY = 15 + Math.random() * 20
    const points = 16
    const startAngle = Math.random() * Math.PI * 2
    const x: number[] = []
    const y: number[] = []
    for (let i = 0; i <= points; i++) {
      const angle = startAngle + (i / points) * Math.PI * 2
      x.push(Math.cos(angle) * radiusX)
      y.push(Math.sin(angle) * radiusY)
    }
    return {
      path: { x, y },
      duration: 4 + Math.random() * 3,
      rotation: [0, Math.random() * 10 - 5, Math.random() * 10 - 5, 0]
    }
  }, [])

  return (
    <motion.div
      key={memory.id}
      className="w-32 h-32 flex items-center justify-center cursor-pointer bg-white/10 dark:bg-gray-800/30 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-full p-3 shadow-md"
      onClick={onClick}
      animate={{ x: path.x, y: path.y, rotate: rotation }}
      transition={{
        x: { duration, repeat: Infinity, ease: 'linear', type: 'tween' },
        y: { duration, repeat: Infinity, ease: 'linear', type: 'tween' },
        rotate: { duration, repeat: Infinity, ease: [0.4, 0, 0.6, 1], type: 'tween' }
      }}
      whileHover={{ scale: 1.5, transition: { duration: 0.2, ease: 'easeOut' } }}
    >
      <p className="text-xs font-bold text-center line-clamp-2">{memory.content}</p>
    </motion.div>
  )
}
