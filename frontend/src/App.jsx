import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@/ThemeContext'
import Layout from '@/components/Layout'
import MemorySpaceLayout from '@/components/MemorySpaceLayout'
import ChatPage from '@/pages/ChatPage'
import MemorySpacePage from '@/pages/MemorySpacePage'
import { AuthProvider } from '@/AuthContext'
import LoginPage from '@/pages/LoginPage'
export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<ChatPage />} />
            <Route path="/:conversationId" element={<ChatPage />} />
          </Route>
          <Route path="/memories" element={<MemorySpaceLayout><MemorySpacePage /></MemorySpaceLayout>} />
        </Routes>
      </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}