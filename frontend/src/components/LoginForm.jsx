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
//import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '@/AuthContext';

export function LoginForm({
  className,
  ...props
}) {
 
  const navigate=useNavigate()
  const [identifier,setIdentifier]=React.useState('')
  const [password,setPassword]=React.useState('')
  const {refreshUser,setUser}=useAuth()
  
  async function loginByCredentials(){
      /*if(!identifier || !password || password.length<6 || !identifier.includes('@')){
        alert('Please enter a valid email/username and password (min 6 characters)')
        return
      }*/
    try{
      const response = await fetch('/api/auth/login',{
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({identifier, password}),
        credentials:'include'
      })
       console.log(response)
       
      if(response.ok){
        await refreshUser()
        navigate('/') 
      }
      else{
        throw new Error('Failed to Authenticate')
      }
    }
    catch(err){
      console.error('Login error:', err)
      alert('Login failed: ' + err.message)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); //prevents default behaviour of form submit which is relaoding the page. 
    await loginByCredentials();
  }

 /* const handleGoogleSuccess = async (credentialResponse) => {
    try{
      console.log(credentialResponse)
      const response = await fetch('/auth/google',{
        method:'POST',
        headers:{
          'Content-Type':'application/json'
        },
        body:JSON.stringify({token:credentialResponse.credential})
      })
      if(response.ok){
        const { user } = await response.json();
        setUser(user)
        console.log(user)
        //await refreshUser()
        navigate('/home')
      }
      else{
        throw new Error('Failed to Authenticate')
      }
    }
    catch(error){
        alert('Login failed: ' + error.message)
    }
  }

  const handleGoogleError=() =>{
    alert('Google login failed')
    console.log('Google login failed')
  }
*/
  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>Login to your account</CardTitle>
          <CardDescription>
            Enter your email/username below to login to your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              <div className="grid gap-3">
                <Label htmlFor="email">Email/Username</Label>
                <Input id="identifier" type="text" placeholder="m@example.com" required 
            onChange={(e)=>setIdentifier(e.target.value)} />
              </div>
              <div className="grid gap-3">
                <div className="flex items-center">
                  <Label htmlFor="password">Password</Label>
                  <a
                    href="#"
                    className="ml-auto inline-block text-sm underline-offset-4 hover:underline">
                    Forgot your password?
                  </a>
                </div>
                <Input id="password" type="password" required onChange={(e)=>setPassword(e.target.value)} />
              </div>
                <Button type="submit" className="w-full">
                  Login
                </Button>
                <div className="after:border-white/30 dark:after:border-white/10 relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t">
                  <span className="bg-background relative z-10 px-2">
                    Or continue with
                  </span>
              </div>
                <div className="flex justify-center">
                  {/*<GoogleLogin onSuccess={handleGoogleSuccess} onError={handleGoogleError} theme='filled_black' shape='pill' width="334"/>*/}
                </div>
              </div>
            
            <div className="mt-4 text-center text-sm">
              Don&apos;t have an account?{" "}
              <Link to="/register" className="underline underline-offset-4">
                Sign up
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
