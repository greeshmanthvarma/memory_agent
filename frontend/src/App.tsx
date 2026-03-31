import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '@/ThemeContext'
import Layout from '@/components/Layout'
import MemorySpaceLayout from '@/components/MemorySpaceLayout'
import ChatPage from '@/pages/ChatPage'
import MemorySpacePage from '@/pages/MemorySpacePage'
import { AuthProvider } from '@/AuthContext'
import LoginPage from '@/pages/LoginPage'
import { Toaster } from '@/components/ui/sonner'
import RegisterPage from '@/pages/RegisterPage'
import LandingPage from '@/pages/LandingPage'
import { TooltipProvider } from '@/components/ui/tooltip'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <TooltipProvider>
          <Toaster />
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/app" element={<Layout />}>
              <Route path="chat" element={<ChatPage />} />
              <Route path="chat/:conversationId" element={<ChatPage />} />
              <Route index element={<Navigate to="/app/chat" replace />} />
            </Route>
            <Route path="/app/memories" element={<MemorySpaceLayout><MemorySpacePage /></MemorySpaceLayout>} />
          </Routes>
          </TooltipProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}
