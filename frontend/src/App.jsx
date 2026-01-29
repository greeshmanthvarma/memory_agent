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

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
      <AuthProvider>
        <Toaster />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<Layout />}>
            <Route path="chat" element={<ChatPage />} />
            <Route path="chat/:conversationId" element={<ChatPage />} />
            <Route index element={<Navigate to="/chat" replace />} />
          </Route>
          <Route path="/memories" element={<MemorySpaceLayout><MemorySpacePage /></MemorySpaceLayout>} />
          {/*<Route path="/memories/list" element={<MemorySpaceLayout><MemorySpaceListPage /></MemorySpaceLayout>} />*/}
        </Routes>
      </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}