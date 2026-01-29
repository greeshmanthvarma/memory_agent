import { RegisterForm } from "@/components/RegisterForm"
import { Sun, Moon } from "lucide-react"
import { useTheme } from '@/ThemeContext';

export default function RegisterPage() {
  const { theme, toggleTheme } = useTheme();
  return (
    <div className="min-h-svh w-full relative bg-background flex items-center justify-center p-6 md:p-10">
      <div className="absolute inset-0 pointer-events-none animate-pulse-radial bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.25),transparent_50%)] dark:bg-[radial-gradient(circle_at_center,rgba(34,197,94,0.15),transparent_50%)] bg-center bg-no-repeat" />
      <div className='absolute top-4 right-4'>
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
      <div className="w-full max-w-sm relative z-10">
        <RegisterForm />
      </div>
    </div>
  )
}
