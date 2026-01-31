import { useEffect } from 'react'
import { useAuth } from '@/AuthContext'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { motion } from 'motion/react'
import { useTheme } from '@/ThemeContext'
import { Sun, Moon, ExternalLinkIcon } from "lucide-react"
import MemoryBubble from '@/components/memory/MemoryBubble'

const LEFT_BUBBLES = [
    { id: 'landing-l-1', content: 'Prefers dark mode for coding', style: { top: '20%', left: '8%' } },
    { id: 'landing-l-2', content: 'Meeting with Alex on Thursday', style: { top: '55%', left: '3%' } },
    { id: 'landing-l-3', content: 'Birthday is in March', style: { top: '75%', left: '12%' } },
]
const RIGHT_BUBBLES = [
    { id: 'landing-r-1', content: 'Working on a memory agent project', style: { top: '30%', right: '8%' } },
    { id: 'landing-r-2', content: 'Likes coffee in the morning', style: { top: '50%', right: '4%' } },
    { id: 'landing-r-3', content: 'Traveling to Paris next month', style: { top: '78%', right: '10%' } },
]

export default function LandingPage(){
    const { user } = useAuth()
    const navigate = useNavigate()
    const { theme, toggleTheme } = useTheme()
    useEffect(()=>{
        if(user){
            navigate('/app/chat')
        }
    },[user])


    return (
        <div className="min-h-svh w-full relative bg-background flex items-center justify-center p-6 md:p-10 overflow-hidden">
            <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.12),transparent_50%)] dark:bg-[radial-gradient(circle_at_center,rgba(34,197,94,0.08),transparent_50%)] bg-center bg-no-repeat" />
            <motion.div 
            initial={{ opacity: 0, filter: 'blur(10px)' }}
            animate={{ opacity: 1, filter: 'blur(0px)' }}
            transition={{ 
                duration: 0.3,
                ease: 'easeInOut',
                delay: 0.5
             }}
            className="hidden lg:block absolute inset-0 pointer-events-none opacity-70 z-[1]">
                {LEFT_BUBBLES.map((m) => (
                    <div key={m.id} className="absolute" style={m.style}>
                        <MemoryBubble memory={m} onClick={() => {}} />
                    </div>
                ))}
                {RIGHT_BUBBLES.map((m) => (
                    <div key={m.id} className="absolute" style={m.style}>
                        <MemoryBubble memory={m} onClick={() => {}} />
                    </div>
                ))}
            </motion.div>
                <motion.div
                className="absolute top-4 w-full flex justify-between"
                initial={{ opacity: 0, filter: 'blur(10px)' }}
                animate={{ opacity: 1, filter: 'blur(0px)' }}
                transition={{ 
                    duration: 0.3,
                    ease: 'easeInOut',
                    delay: 0.5
                 }}
                >
                    <div className="flex items-center justify-center gap-2 px-4">
                        <p className="text-2xl font-bold text-neutral-700 dark:text-white">Coherence</p>
                    </div>
                    
                <div className=" flex items-center justify-center gap-2 px-4">
                    <Link to="/register">
                        <Button className="cursor-pointer">
                            Get started
                        </Button>
                    </Link>
                    <Link to="/login">
                        <Button variant="outline" className="cursor-pointer">
                            Sign in
                        </Button>
                    </Link>
                    <a href="https://github.com/greeshmanthvarma/memory_agent" target="_blank" rel="noopener noreferrer">
                        <Button variant="outline" className="cursor-pointer">
                            GitHub
                            <ExternalLinkIcon/>
                        </Button>
                    </a>
                    <button
                        onClick={toggleTheme}
                        className="p-2 rounded-full cursor-pointer bg-white/30 dark:bg-gray-900/50 backdrop-blur-xl border border-white/30 dark:border-white/10 hover:bg-white/40 dark:hover:bg-gray-900/60 transition-all"
                        aria-label="Toggle theme"
                    >
                        {theme === 'dark' ? (
                        <Sun className="w-5 h-5 text-black dark:text-white" />
                        ) : (
                        <Moon className="w-5 h-5 text-black dark:text-white" />
                        )}
                    </button>
                    </div>
                </motion.div>
                <motion.div 
                initial={{ opacity: 0, y: 24, filter: 'blur(4px)' }}
                animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                transition={{ 
                    duration: 0.5,
                    ease: 'easeOut',
                    delay: 0.3
                 }}
                className="relative z-10 flex items-center justify-center w-full max-w-6xl mx-auto px-4">
                    <div className="flex flex-col items-center justify-center gap-4 flex-1 min-w-0">
                    <h1 className="text-2xl px-4 md:text-4xl lg:text-5xl font-bold text-neutral-700 dark:text-white max-w-4xl leading-relaxed lg:leading-snug text-center mx-auto">
                        An AI that{' '}
                        <span className="relative inline-block px-2">
                            <motion.span
                            className="absolute inset-0 rounded-md bg-indigo-500/30 dark:bg-indigo-400/30"
                            initial={{ scaleX: 0 }}
                            animate={{ scaleX: 1 }}
                            transition={{
                                duration: 0.6,
                                ease: 'easeInOut',
                                delay: 1
                            }}
                            style={{ transformOrigin: 'left' }}
                            />
                            <span className="relative z-10 font-extrabold text-foreground">
                            remembers
                            </span>
                        </span>{' '}
                        across conversations.
                    </h1>
                    <p className="text-md text-neutral-500 dark:text-neutral-400 max-w-2xl text-center mx-auto">
                        Persistent memory powered by semantic search and intelligent recall.
                    </p>
                    </div>
                </motion.div>
        </div>
    )
}