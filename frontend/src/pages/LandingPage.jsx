import { useEffect, useState, useRef, useLayoutEffect } from 'react'
import { useAuth } from '@/AuthContext'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { motion, useInView } from 'motion/react'
import { useTheme } from '@/ThemeContext'
import { Sun, Moon, ExternalLinkIcon, MousePointer, PanelRight, SquarePen, Bubbles } from "lucide-react"
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
    const { user,refreshUser } = useAuth()
    const navigate = useNavigate()
    const [isDemoLoading, setIsDemoLoading] = useState(false)
    const [isChatHovered, setIsChatHovered] = useState(false)
    const [isSummaryHovered, setIsSummaryHovered] = useState(false)
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const summarizeConversationRef = useRef(null)
    const summaryOverlayRef = useRef(null)
    const summaryChatRef = useRef(null)
    const { theme, toggleTheme } = useTheme()
    const CURSOR_SIZE = 16 

    useEffect(()=>{
        if(user){
            navigate('/app/chat')
        }
    },[user])

  const [cursorStart, setCursorStart] = useState({ x: 0, y: 0 })
  const bentoRef = useRef(null)
  const isBentoInView = useInView(bentoRef, { amount: 0.2 })

  const bentoContainer = {
    hidden: {},
    show: { transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
  }
  const bentoItem = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeInOut' } },
  }

  useLayoutEffect(() => {
    if (!isSummaryHovered || !summarizeConversationRef.current || !summaryOverlayRef.current || !summaryChatRef.current) return
    const measure = () => {
      const overlay = summaryOverlayRef.current
      const button = summarizeConversationRef.current
      const chatDiv = summaryChatRef.current
      if (!overlay || !button || !chatDiv) return
      const overlayRect = overlay.getBoundingClientRect()
      const buttonRect = button.getBoundingClientRect()
      const chatRect = chatDiv.getBoundingClientRect()
      const centerX = (chatRect.left - overlayRect.left) + (chatRect.width / 2) - (CURSOR_SIZE / 2)
      const centerY = (chatRect.top - overlayRect.top) + (chatRect.height / 2) - (CURSOR_SIZE / 2)
      setCursorStart({ x: centerX, y: centerY })
      setPosition({
        x: (buttonRect.left - overlayRect.left) + (buttonRect.width / 2) - (CURSOR_SIZE / 2),
        y: (buttonRect.top - overlayRect.top) + (buttonRect.height / 2) - (CURSOR_SIZE / 2),
      })
    }
    measure()
    const t = requestAnimationFrame(measure)
    return () => cancelAnimationFrame(t)
  }, [isSummaryHovered]) 

    async function handleTryDemo() {
        setIsDemoLoading(true)
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ identifier: 'demo', password: 'test123' }),
                credentials: 'include',
            })
            if (response.ok) {
                await refreshUser()
                toast.success('Demo loaded. Explore the app.')
                navigate('/app/chat')
            } else {
                const data = await response.json().catch(() => ({}))
                toast.error(data.detail || 'Demo unavailable. Please sign up to try.')
            }
        } catch (err) {
            toast.error('Demo unavailable. Please sign up to try.')
        } finally {
            setIsDemoLoading(false)
        }
    }

    const responseContainer = {
        hidden : {},
        show : {transition : {staggerChildren : 0.03}}
    }

    const responseItem = {
        hidden : {opacity : 0},
        show : {opacity : 1}
    }

    const responseText = "Since you enjoy hiking, this weekend could be a great opportunity to hit the trails! Whether it's a well-known spot or a new path you've been wanting to explore, being in nature can be really refreshing. If you're looking for something else, maybe consider grabbing a coffee at your favorite café..."

    return (
        <div className="min-h-svh w-full relative bg-background flex flex-col overflow-y-auto">
            <section className="min-h-svh w-full flex flex-col items-center justify-center p-6 md:p-10 relative">
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
                    <Button
                        size="lg"
                        variant="outline"
                        className="mt-4 cursor-pointer"
                        onClick={handleTryDemo}
                        disabled={isDemoLoading}
                    >
                        {isDemoLoading ? 'Loading...' : 'Try demo'}
                    </Button>
                    </div>
                </motion.div>
            </section>
            <section className="w-full max-w-7xl mx-auto px-4 mt-24 md:mt-32 mb-24 md:mb-32">
                <motion.div
                    ref={bentoRef}
                    className="grid grid-cols-3 grid-rows-[12rem_18rem] gap-2"
                    initial="hidden"
                    animate={isBentoInView ? 'show' : 'hidden'}
                    variants={bentoContainer}
                >
                    <motion.div
                        variants={bentoItem}
                        className="row-span-2 min-w-[12rem] w-[24rem] flex flex-col items-center justify-center backdrop-blur-xl border border-gray-200/30 dark:border-white/10 rounded-xl shadow-[0_1px_1px_rgba(0,0,0,0.05),0_4px_6px_rgba(34,42,53,0.04),0_24px_68px_rgba(47,48,55,0.05),0_2px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_1px_1px_rgba(255,255,255,0.04),0_4px_6px_rgba(230,230,230,0.03),0_24px_68px_rgba(220,220,220,0.04),0_2px_3px_rgba(255,255,255,0.03)]"
                        onMouseEnter={() => setIsChatHovered(true)}
                        onMouseLeave={() => setIsChatHovered(false)}
                    >
                        <p className="text-2xl font-bold text-center line-clamp-2 mb-2 mt-6">
                            Chat with context
                        </p>
                        <p className="text-sm text-muted-foreground text-center mb-4 px-4">
                            The AI uses your memories when needed to personalize responses.
                        </p>
                        <div className="flex-1 w-full mt-10 flex flex-col gap-4">
                            <motion.div
                                className="flex justify-end w-full"
                                animate={{ y: isChatHovered ? -8 : 0 }}
                                transition={{ duration: 0.3, ease: 'easeInOut' }}
                            >
                                <div className="bg-primary/10 text-foreground px-4 py-2 mr-2 rounded-full w-fit">
                                    <p className="text-sm">What should I do this weekend?</p>
                                </div>
                            </motion.div>
                            <motion.div 
                            initial="hidden"
                            animate={isChatHovered ? "show" : "hidden"}
                            variants={responseContainer}
                            className="flex flex-wrap justify-start w-full ml-4 max-w-[85%] gap-y-0.5">
                                {
                                    responseText.split(' ').map((word, index) => (
                                        <motion.span key={index} className="text-sm" variants={responseItem} style={{marginRight: '0.25em'}}>
                                            {word}
                                        </motion.span>
                                    ))
                                }
                            </motion.div>
                        </div>
                    </motion.div>
                    <motion.div
                    variants={bentoItem}
                    onMouseEnter={() => setIsSummaryHovered(true)}
                    onMouseLeave={() => setIsSummaryHovered(false)}
                    className="col-span-2 relative flex items-center justify-center h-[12rem] w-full border border-gray-200/30 dark:border-white/10 rounded-xl shadow-[0_1px_1px_rgba(0,0,0,0.05),0_4px_6px_rgba(34,42,53,0.04),0_24px_68px_rgba(47,48,55,0.05),0_2px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_1px_1px_rgba(255,255,255,0.04),0_4px_6px_rgba(230,230,230,0.03),0_24px_68px_rgba(220,220,220,0.04),0_2px_3px_rgba(255,255,255,0.03)]">
                                <motion.p 
                                initial={{ opacity: 1, filter: 'blur(0px)' }}
                                animate={{ opacity: isSummaryHovered ? 0.2 : 1 , filter: isSummaryHovered ? 'blur(2px)' : 'blur(0px)' }}
                                transition={{ duration: 0.3, ease: 'easeInOut' }}
                                className="text-2xl font-bold text-center">
                                    Create memories from Conversations
                                </motion.p>
                            <motion.div 
                            initial={{ opacity: 0.2, filter: 'blur(2px)' }}
                            animate={{ opacity: isSummaryHovered ? 1 : 0 , filter: isSummaryHovered ? 'blur(0px)' : 'blur(10px)' }}
                            transition={{ duration: 0.3, ease: 'easeInOut' }}
                            className="absolute inset-0 flex pointer-events-none">
                                <div ref={summaryOverlayRef} className="absolute inset-0 flex">
                                {isSummaryHovered && (cursorStart.x > 0 || cursorStart.y > 0) && (
                                <motion.div
                                    key={`cursor-${cursorStart.x}-${cursorStart.y}`}
                                    initial={{ left: cursorStart.x, top: cursorStart.y, scale: 1 }}
                                    animate={{ left: position.x, top: position.y, scale: [1, 0.85, 1] }}
                                    transition={{
                                      left: { duration: 0.75, delay: 0.3, ease: 'easeInOut' },
                                      top: { duration: 0.75, delay: 0.3, ease: 'easeInOut' },
                                      scale: { duration: 0.3, delay: 1.05, ease: 'easeOut' },
                                    }}
                                    className="absolute z-10 w-4 h-4 text-foreground origin-center"
                                >
                                    <MousePointer className="w-4 h-4" stroke="currentColor" />
                                </motion.div>
                                )}
                                <div className = "flex flex-col w-[3rem] border-r gap-y-8 pt-6">
                                    <div className="flex flex-col items-center justify-center gap-2 mb-2">
                                        <PanelRight className="w-4 h-4"/>
                                    </div>
                                    <div className="flex flex-col items-center justify-center gap-y-6">
                                        <SquarePen className="w-4 h-4"/>
                                        <Bubbles className="w-4 h-4"/>
                                    </div>
                                    
                                 </div>   
                                <div ref={summaryChatRef} className="flex flex-1 flex-col">
                                    <div className="flex h-[3.5rem] border-b relative items-center justify-between px-2">
                                        <div 
                                        ref={summarizeConversationRef}
                                        className="flex text-xs items-center justify-center px-4 py-2 text-muted-foreground rounded-sm border"> 
                                            Summarize Conversation
                                        </div>
                                        {
                                            theme === 'dark' ? (
                                                <Sun className="w-5 h-5 text-black dark:text-white pr-2" />
                                            ) : (
                                                <Moon className="w-5 h-5 text-black dark:text-white pr-2" />
                                            )
                                        }
                                        
                                    </div>
                                    <div className="flex flex-1 flex-col mt-6 gap-4">
                                        <div className="flex justify-end">
                                            <div className="bg-primary/10 text-foreground text-sm px-4 py-2 mr-2 rounded-full w-fit">
                                                <p>What should I do this weekend?</p>
                                            </div>
                                        </div>
                                        
                                        <div className="flex justify-start text-sm text-foreground ml-4">
                                            <p>You should be hiring me!</p>
                                        </div>
                                    </div>
                                    </div>
                                </div>
                            </motion.div>
                    </motion.div>
                    <motion.div variants={bentoItem} className="col-start-2 row-start-2 flex flex-col items-center justify-center gap-1 border border-gray-200/30 dark:border-white/10 rounded-xl min-h-0 p-4 mt-4 mr-2 shadow-[0_1px_1px_rgba(0,0,0,0.05),0_4px_6px_rgba(34,42,53,0.04),0_24px_68px_rgba(47,48,55,0.05),0_2px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_1px_1px_rgba(255,255,255,0.04),0_4px_6px_rgba(230,230,230,0.03),0_24px_68px_rgba(220,220,220,0.04),0_2px_3px_rgba(255,255,255,0.03)]">
                        <p className="text-lg font-semibold text-center">Semantic search</p>
                        <p className="text-xs text-muted-foreground text-center">Powered by RAG, find by relevant memories by meaning</p>
                    </motion.div>
                    <motion.div variants={bentoItem} className="col-start-3 row-start-2 flex flex-col items-center justify-center gap-1 border border-gray-200/30 dark:border-white/10 rounded-xl min-h-0 p-4 mt-4 ml-2 shadow-[0_1px_1px_rgba(0,0,0,0.05),0_4px_6px_rgba(34,42,53,0.04),0_24px_68px_rgba(47,48,55,0.05),0_2px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_1px_1px_rgba(255,255,255,0.04),0_4px_6px_rgba(230,230,230,0.03),0_24px_68px_rgba(220,220,220,0.04),0_2px_3px_rgba(255,255,255,0.03)]">
                        <p className="text-lg font-semibold text-center">Log memories manually</p>
                        <p className="text-xs text-muted-foreground text-center">Add detailed memories, facts or preferences anytime</p>
                    </motion.div>
                </motion.div>
            </section>
            <footer className="w-full border-t border-white/30 dark:border-white/10 py-8 mt-16">
                <div className="w-full max-w-7xl mx-auto px-4 flex flex-col items-center gap-2 text-center">
                    <p className="text-sm text-muted-foreground">
                        Built with React · Vite · Tailwind CSS · Motion · FastAPI · PostgreSQL · Qdrant · OpenAI
                    </p>
                    <p className="text-xs text-muted-foreground/80">
                        © {new Date().getFullYear()} Coherence · Portfolio project
                    </p>
                </div>
            </footer>
        </div>
    )
}