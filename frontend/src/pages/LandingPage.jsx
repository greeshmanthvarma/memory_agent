import { useEffect, useState, useRef, useLayoutEffect } from 'react'
import { useAuth } from '@/AuthContext'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { motion } from 'motion/react'
import { useTheme } from '@/ThemeContext'
import { Sun, Moon, ExternalLinkIcon, MousePointer, PanelRight, SquarePen, Bubbles, MessageSquare, Search, Reply, RefreshCw, ArrowRightIcon} from "lucide-react"
import MemoryBubble from '@/components/memory/MemoryBubble'
import AnimatedPulse from '@/components/animatedPulse'
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
    const [isReflectionHovered, setIsReflectionHovered] = useState(false)
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const pageRef = useRef(null)
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
                body: JSON.stringify({ identifier: 'Demo', password: 'demo1234' }),
                credentials: 'include',
            })
            if (response.ok) {
                await refreshUser()
                toast.success('Demo loaded. Explore the app.')
                navigate('/app/chat')
            } else {
                toast.error("Couldn't load demo. The database might be napping (free tier :( ). Give it a few seconds and try again!")
            }
        } catch (err) {
            toast.error("Couldn't connect. Check your connection, or wait a moment. Server might be waking up (free tier :( ). Try again!")
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
        <div ref={pageRef} className="min-h-svh w-full bg-background relative flex flex-col overflow-y-auto">
            <div className="fixed size-full inset-0 z-0 pointer-events-none">
                <AnimatedPulse theme={theme} />
            </div>
            <section className="min-h-svh w-full flex flex-col items-center justify-center p-6 md:p-10 relative z-10">
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
                className="absolute top-3 sm:top-4 w-full flex justify-between items-center gap-1 px-2 sm:px-4 min-w-0"
                initial={{ opacity: 0, filter: 'blur(10px)' }}
                animate={{ opacity: 1, filter: 'blur(0px)' }}
                transition={{ 
                    duration: 0.3,
                    ease: 'easeInOut',
                    delay: 0.5
                 }}
                >
                    <div className="flex min-w-0 shrink items-center gap-2 px-1 sm:px-4">
                        <img src="/logo.svg" alt="Coherence" className="h-6 w-6 flex-shrink-0 dark:invert" />
                        <p className="text-xl sm:text-2xl font-bold text-neutral-700 dark:text-white truncate">Coherence</p>
                    </div>
                    
                <div className="flex shrink-0 items-center justify-center gap-1 sm:gap-2 pl-1">
                    <Link to="/register">
                        <Button size="sm" className="cursor-pointer text-xs sm:text-sm h-7 sm:h-9 px-1.5 sm:px-4">
                            Get started
                        </Button>
                    </Link>
                    <Link to="/login">
                        <Button size="sm" variant="outline" className="cursor-pointer text-xs sm:text-sm h-8 sm:h-9 px-2 sm:px-4">
                            Sign in
                        </Button>
                    </Link>
                    <a href="https://github.com/greeshmanthvarma/memory_agent" target="_blank" rel="noopener noreferrer">
                        <Button size="sm" variant="outline" className="cursor-pointer text-xs sm:text-sm h-7 sm:h-9 px-1.5 sm:px-4">
                            <span className="sm:hidden">Git</span>
                            <span className="hidden sm:inline">GitHub</span>
                            <ExternalLinkIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4 ml-0.5 hidden sm:inline" />
                        </Button>
                    </a>
                    <button
                        onClick={toggleTheme}
                        className="p-1.5 sm:p-2 rounded-full cursor-pointer bg-white/30 dark:bg-gray-900/50 backdrop-blur-xl border border-white/30 dark:border-white/10 hover:bg-white/40 dark:hover:bg-gray-900/60 transition-all"
                        aria-label="Toggle theme"
                    >
                        {theme === 'dark' ? (
                        <Sun className="w-4 h-4 sm:w-5 sm:h-5 text-black dark:text-white" />
                        ) : (
                        <Moon className="w-4 h-4 sm:w-5 sm:h-5 text-black dark:text-white" />
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
                className="relative z-10 flex items-center justify-center w-full max-w-6xl mx-auto px-3 sm:px-4">
                    <div className="flex flex-col items-center justify-center gap-2 sm:gap-3 flex-1 min-w-0">
                    <h1 className="text-2xl px-4 md:text-4xl lg:text-5xl font-bold text-neutral-700 dark:text-white max-w-4xl leading-tight tracking-tight text-center mx-auto">
                        An AI that{' '}
                        <span className="relative inline-block px-2">
                            <motion.span
                            className="absolute inset-0 rounded-md bg-indigo-500/30 dark:bg-green-500/20"
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
                            remembers and adapts
                            </span>
                        </span>{' '}
                        across conversations.
                    </h1>
                    <p className="text-sm sm:text-base text-neutral-500 dark:text-neutral-400 max-w-2xl text-center mx-auto leading-snug tracking-tight">
                        Persistent memory powered by semantic search and intelligent recall.
                    </p>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                size="lg"
                                variant="outline"
                                className="mt-3 sm:mt-4 cursor-pointer text-sm sm:text-base"
                                onClick={handleTryDemo}
                                disabled={isDemoLoading}
                            >
                                {isDemoLoading ? 'Loading...' : 'Try demo'}
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p className="text-xs text-muted-foreground">If it doesn&apos;t load, try again. The database may be waking up.</p>
                        </TooltipContent>
                    </Tooltip>
                    </div>
                </motion.div>
            </section>
            <section className="w-full max-w-4xl mx-auto px-4 mt-16 md:mt-20 relative z-10">
                <motion.h2
                    initial={{ opacity: 0, y: 12 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0, root: pageRef }}
                    transition={{ duration: 0.4 }}
                    className="text-sm font-medium text-center text-muted-foreground uppercase tracking-widest mb-10"
                >
                    When you send a message
                </motion.h2>
                <div className="flex flex-col sm:flex-row justify-center items-center gap-6 sm:gap-0">
                    {[
                        { icon: MessageSquare, label: "You send a message" },
                        { icon: Search, label: "Relevant memories are found" },
                        { icon: Reply, label: "AI responds with context" },
                        { icon: RefreshCw, label: "Memories updated in background" },
                    ].map((step, i) => (
                        <div key={step.label} className="flex sm:flex-row flex-col items-center">
                            <motion.div
                                initial={{ opacity: 0, y: 16 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true, amount: 0, root: pageRef }}
                                transition={{ duration: 0.35, ease: "easeOut", delay: 0.1 + i * 0.12 }}
                                className="flex flex-col items-center gap-2.5 w-[8rem]"
                            >
                                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-background shadow-sm">
                                    <step.icon className="h-4 w-4 text-muted-foreground" />
                                </div>
                                <p className="text-xs text-center text-muted-foreground leading-snug">{step.label}</p>
                            </motion.div>
                            {
                            i < 3 && (
                                <motion.div
                                initial={{ opacity: 0, y: 16 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true, amount: 0, root: pageRef }}
                                transition={{ duration: 0.35, ease: "easeOut", delay: 0.1 + i * 0.12 }}
                                className="flex h-10 w-10 items-center justify-center shadow-sm px-2"
                                >
                                    <ArrowRightIcon className="w-4 h-4 text-muted-foreground" />
                                </motion.div>
                            )}
                        </div>
                    ))}
                </div>
            </section>
            <section className="w-full max-w-7xl mx-auto px-4 mt-24 md:mt-32 mb-24 md:mb-32 relative z-10">
                <div className="grid grid-cols-1 md:grid-cols-3 md:grid-rows-[12rem_18rem] gap-2">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, amount: 0, root: pageRef }}
                        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.05 }}
                        className="w-full min-h-[18rem] md:row-span-2 md:min-w-[12rem] md:w-[24rem] md:min-h-0 flex flex-col items-center justify-center backdrop-blur-xl border border-gray-200/30 dark:border-white/10 rounded-xl shadow-[0_1px_1px_rgba(0,0,0,0.05),0_4px_6px_rgba(34,42,53,0.04),0_24px_68px_rgba(47,48,55,0.05),0_2px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_1px_1px_rgba(255,255,255,0.04),0_4px_6px_rgba(230,230,230,0.03),0_24px_68px_rgba(220,220,220,0.04),0_2px_3px_rgba(255,255,255,0.03)]"
                        onMouseEnter={() => setIsChatHovered(true)}
                        onMouseLeave={() => setIsChatHovered(false)}
                    >
                        <motion.div 
                        animate={{ opacity: isChatHovered ? 0.5 : 1 , filter: isChatHovered ? 'blur(2px)' : 'blur(0px)' }}
                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                        >
                            <p className="text-2xl font-bold text-center line-clamp-2 mb-2 mt-6">
                                Chat with context
                            </p>
                            <p className="text-sm text-muted-foreground text-center mb-4 px-4">
                                The AI uses your memories to personalize responses.
                            </p>
                        </motion.div>
                        
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
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0, root: pageRef }}
                    transition={{ duration: 0.4, ease: 'easeOut', delay: 0.13 }}
                    onMouseEnter={() => setIsSummaryHovered(true)}
                    onMouseLeave={() => setIsSummaryHovered(false)}
                    className="md:col-span-2 relative flex items-center justify-center min-h-[12rem] md:h-[12rem] w-full border border-gray-200/30 dark:border-white/10 rounded-xl shadow-[0_1px_1px_rgba(0,0,0,0.05),0_4px_6px_rgba(34,42,53,0.04),0_24px_68px_rgba(47,48,55,0.05),0_2px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_1px_1px_rgba(255,255,255,0.04),0_4px_6px_rgba(230,230,230,0.03),0_24px_68px_rgba(220,220,220,0.04),0_2px_3px_rgba(255,255,255,0.03)]">
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
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, amount: 0, root: pageRef }}
                        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.21 }}
                        onMouseEnter={() => setIsReflectionHovered(true)}
                        onMouseLeave={() => setIsReflectionHovered(false)}
                        className="relative flex flex-col items-center justify-center min-h-[14rem] md:min-h-0 md:col-span-2 md:col-start-2 md:row-start-2 border border-gray-200/30 dark:border-white/10 rounded-xl overflow-hidden p-5 gap-2 shadow-[0_1px_1px_rgba(0,0,0,0.05),0_4px_6px_rgba(34,42,53,0.04),0_24px_68px_rgba(47,48,55,0.05),0_2px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_1px_1px_rgba(255,255,255,0.04),0_4px_6px_rgba(230,230,230,0.03),0_24px_68px_rgba(220,220,220,0.04),0_2px_3px_rgba(255,255,255,0.03)]"
                    >
                        <motion.p
                            animate={{ opacity: isReflectionHovered ? 0.2 : 1, filter: isReflectionHovered ? 'blur(2px)' : 'blur(0px)' }}
                            transition={{ duration: 0.3, ease: 'easeInOut' }}
                            className="text-2xl font-bold text-center"
                        >
                            Memories evolve automatically
                        </motion.p>
                        <motion.p
                            animate={{ opacity: isReflectionHovered ? 0.2 : 1, filter: isReflectionHovered ? 'blur(2px)' : 'blur(0px)' }}
                            transition={{ duration: 0.3, ease: 'easeInOut' }}
                            className="text-sm text-muted-foreground text-center"
                        >
                            After every response, a reflection model creates, updates, or merges memories in the background.
                        </motion.p>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: isReflectionHovered ? 1 : 0, filter: isReflectionHovered ? 'blur(0px)' : 'blur(4px)' }}
                            transition={{ duration: 0.3, ease: 'easeInOut' }}
                            className="absolute inset-0 flex items-stretch justify-center gap-3 px-5 py-5 pointer-events-none"
                        >
                            {[
                                {
                                    label: 'Created',
                                    before: 'Just give me the short version, I hate long explanations.',
                                    after: 'Prefers concise answers over long explanations.',
                                },
                                {
                                    label: 'Updated',
                                    before: 'Enjoys hiking on weekends.',
                                    after: 'Enjoys hiking. Recently tried trail running.',
                                },
                                {
                                    label: 'Merged',
                                    before: ['Works in ML.', 'Interested in NLP.'],
                                    after: 'Works in ML, currently focused on NLP and RAG systems.',
                                },
                            ].map((item, i) => (
                                <motion.div
                                    key={item.label}
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: isReflectionHovered ? 1 : 0, y: isReflectionHovered ? 0 : 8 }}
                                    transition={{ duration: 0.3, ease: 'easeOut', delay: isReflectionHovered ? 0.05 + i * 0.07 : 0 }}
                                    className="flex flex-col gap-2 flex-1 rounded-lg border border-border bg-muted/30 px-3 py-2.5"
                                >
                                    <span className="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground">{item.label}</span>
                                    <div className="flex flex-col gap-1">
                                        <p className="text-[10px] text-muted-foreground uppercase tracking-widest">{item.label === 'Created' ? 'Message' : 'Before'}</p>
                                        {Array.isArray(item.before) ? (
                                            <div className="flex flex-col gap-0.5">
                                                {item.before.map((b, j) => (
                                                    <p key={j} className="text-xs text-muted-foreground line-through leading-relaxed">{b}</p>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className={`text-xs leading-relaxed ${item.label === 'Created' ? 'text-muted-foreground italic' : 'text-muted-foreground line-through'}`}>{item.before}</p>
                                        )}
                                    </div>
                                    <div className="w-full h-px bg-border/50" />
                                    <div className="flex flex-col gap-1">
                                        <p className="text-[10px] text-muted-foreground uppercase tracking-widest">After</p>
                                        <p className="text-xs text-foreground leading-relaxed">{item.after}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </motion.div>
                    </motion.div>
                </div>
            </section>
            <footer className="w-full border-t border-border py-8 mt-16 relative z-10">
                <div className="w-full max-w-7xl mx-auto px-4 flex flex-col items-center gap-2 text-center">
                    <p className="text-sm text-muted-foreground">
                        Built with React · FastAPI · LangGraph · PostgreSQL · Qdrant · OpenAI
                    </p>
                    <p className="text-xs text-muted-foreground/60">
                        © {new Date().getFullYear()} Greeshmanth Varma · Portfolio project
                    </p>
                </div>
            </footer>
        </div>
    )
}