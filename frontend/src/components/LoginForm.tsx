import * as React from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from '@/AuthContext'
import { toast } from "sonner"

export function LoginForm({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  const navigate = useNavigate()
  const [identifier, setIdentifier] = React.useState('')
  const [password, setPassword] = React.useState('')
  const { refreshUser } = useAuth()

  async function loginByCredentials() {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password }),
        credentials: 'include'
      })
      if (response.ok) {
        await refreshUser()
        toast.success('Login successful')
        navigate('/app/chat')
      } else {
        const errorData = await response.json().catch(() => ({}))
        throw new Error((errorData as { detail?: string }).detail || 'Failed to authenticate')
      }
    } catch (err) {
      console.error('Login error:', err)
      toast.error('Login failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await loginByCredentials()
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>Login to your account</CardTitle>
          <CardDescription>Enter your email/username below to login to your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              <div className="grid gap-3">
                <Label htmlFor="identifier">Email/Username</Label>
                <Input id="identifier" type="text" placeholder="m@example.com" required onChange={(e) => setIdentifier(e.target.value)} />
              </div>
              <div className="grid gap-3">
                <div className="flex items-center">
                  <Label htmlFor="password">Password</Label>
                  <Link to="/forgot-password" className="ml-auto inline-block text-sm underline-offset-4 hover:underline cursor-not-allowed">
                    Forgot your password?
                  </Link>
                </div>
                <Input id="password" type="password" required onChange={(e) => setPassword(e.target.value)} />
              </div>
              <Button type="submit" className="w-full">Login</Button>
              <div className="after:border-white/30 dark:after:border-white/10 relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t">
                <span className="bg-background relative z-10 px-2">Or continue with</span>
              </div>
              <div className="flex justify-center" />
            </div>
            <div className="mt-4 text-center text-sm">
              Don&apos;t have an account?{" "}
              <Link to="/register" className="underline underline-offset-4">Sign up</Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
