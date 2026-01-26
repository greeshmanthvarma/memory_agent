export default function MemorySpaceLayout({ children }) {
  return (
    <div className="min-h-screen bg-white dark:bg-black relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none animate-pulse-radial bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.25),transparent_50%)] dark:bg-[radial-gradient(circle_at_center,rgba(34,197,94,0.15),transparent_50%)] bg-center bg-no-repeat">
      </div>
      <div className="relative z-10 h-screen">
        {children}
      </div>
    </div>
  )
}
