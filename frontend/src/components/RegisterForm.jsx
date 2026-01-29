import * as React from 'react';
import {useNavigate, Link} from 'react-router-dom'
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from '@/AuthContext';
import { toast } from "sonner"

export function RegisterForm({
  className,
  ...props
}) {
 
  const navigate=useNavigate()
  const [email,setEmail]=React.useState('')
  const [password,setPassword]=React.useState('')
  const [username,setUsername]=React.useState('')
  const { refreshUser } = useAuth()
  const [isLoading, setIsLoading] = React.useState(false)
  
  async function registerByCredentials(){
      if(!email || !username || !password || password.length<6){
        toast.error('Please enter a valid email, username, and password (min 6 characters)')
        return
      }
    try{
      setIsLoading(true)
      const response = await fetch('/api/auth/register',{
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, username, password}),
        credentials:'include'
      })
       
      if(response.ok){
        await refreshUser()
        toast.success('Registration successful')
        navigate('/') 
      }
      else{
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to register')
      }
    }
    catch(err){
        toast.error('Registration failed: ' + err.message)
        console.error('Registration error:', err)
      
    }
    finally{
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); //prevents default behaviour of form submit which is relaoding the page. 
    await registerByCredentials();
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>Sign up for an account</CardTitle>
          <CardDescription>
            Enter your details below to sign up for an account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              <div className="grid gap-3">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="m@example.com" required 
            onChange={(e)=>setEmail(e.target.value)} />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="username">Username</Label>
                <Input id="username" type="text" placeholder="username" required 
            onChange={(e)=>setUsername(e.target.value)} />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" required onChange={(e)=>setPassword(e.target.value)} />
              </div>
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Creating account...' : 'Sign up'}
              </Button>
            
            <div className="mt-4 text-center text-sm">
              Already have an account?{" "}
              <Link to="/login" className="underline underline-offset-4">
                Login
              </Link>
            </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )

}