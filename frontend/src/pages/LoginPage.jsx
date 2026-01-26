import { LoginForm } from "@/components/LoginForm"
import { Sun, Moon } from "lucide-react"
import { useTheme } from '@/ThemeContext';
export default function LoginPage() {
  const { theme, toggleTheme } = useTheme();
  return (
    <div className="min-h-svh w-full relative bg-black flex items-center justify-center p-6 md:p-10">
      <div
        className="absolute inset-0 z-0"
      />
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
        <LoginForm />
      </div>
    </div>
  )
}
