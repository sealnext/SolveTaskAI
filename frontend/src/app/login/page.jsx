"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSession, signIn } from 'next-auth/react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { LockIcon, MailIcon, AlertCircle } from 'lucide-react'
import { FaApple, FaGoogle, FaGithub } from 'react-icons/fa'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const [pending, setPending] = useState(false)
  const router = useRouter()
  const { data: session, status } = useSession()

  useEffect(() => {
    if (status === 'authenticated') {
      router.push('/chat')
    }
  }, [status, router])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setPending(true)
    setErrorMessage(null)

    try {
      const res = await signIn('credentials', {
        redirect: false,
        username: email,
        password,
      })

      if (res?.error) {
        setErrorMessage(res.error)
        setPending(false)
      } else {
        setPending(false)
        router.push("/chat")
      }
    } catch (error) {
      console.error("Login error:", error)
      setErrorMessage("An unexpected error occurred. Please try again.")
      setPending(false)
    }
  }

  const handleGoogleLogin = () => {
    signIn('google', { callbackUrl: '/chat' })
  }

  const handleGithubLogin = () => {
    signIn('github', { callbackUrl: '/chat' })
  }

  const LoginStatusButton = () => {
    if (session) {
      return (
        <div className="text-center mt-4">
          <p>Signed in as {session.user.name || session.user.email}</p>
          <Button onClick={() => signOut()} className="mt-2">Sign out</Button>
        </div>
      )
    }
    return null 
  }

  if (status === 'loading' || status === 'authenticated') {
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md bg-backgroundSecondary shadow-lg border-none">
        <CardHeader>
          <h1 className="text-2xl font-semibold text-center text-foreground">Welcome Back</h1>
          <p className="text-center text-muted-foreground mt-2">Please enter your details to sign in.</p>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center space-x-4 mb-6">
            <Button 
              variant="outline" 
              className="w-12 h-12 rounded-full p-0 flex items-center justify-center"
              onClick={() => signIn('apple', { callbackUrl: '/chat' })}
            >
              <FaApple className="h-5 w-5" />
            </Button>
            <Button 
              variant="outline" 
              className="w-12 h-12 rounded-full p-0 flex items-center justify-center"
              onClick={handleGoogleLogin}
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
                <path d="M1 1h22v22H1z" fill="none" />
              </svg>
            </Button>
            <Button 
              variant="outline" 
              className="w-12 h-12 rounded-full p-0 flex items-center justify-center"
              onClick={handleGithubLogin}
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
              </svg>
            </Button>
          </div>
          
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-muted"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-backgroundSecondary px-2 text-muted-foreground">OR</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-foreground-secondary">Email</Label>
              <Input
                id="email"
                type="email"
                icon={MailIcon}
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-foreground-secondary">Password</Label>
              <Input
                id="password"
                type="password"
                icon={LockIcon}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(checked) => setRememberMe(checked)}
                  className="border-muted bg-background-secondary checked:bg-primary" />
                <Label
                  htmlFor="remember"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-foreground-secondary">
                  Remember me
                </Label>
              </div>
              <Button variant="link" className="text-sm text-primary p-0 hover:text-secondary">
                Forgot password?
              </Button>
            </div>
            <Button 
              type="submit" 
              className="w-full bg-primary hover:bg-secondary text-foreground" 
              disabled={pending}
            >
              {pending ? 'Connecting...' : 'Login'}
            </Button>
            {errorMessage && (
              <div className="flex items-center space-x-2 text-accent">
                <AlertCircle size={18} />
                <p className="text-sm">{errorMessage}</p>
              </div>
            )}
          </form>
        </CardContent>
        <CardFooter className="justify-center flex-col">
          <p className="text-sm text-foreground-secondary">
            Don't have an account?{' '}
            <Button variant="link" className="p-0 text-primary hover:text-secondary" onClick={() => router.push('/signup')}>
              Sign up
            </Button>
          </p>
          <LoginStatusButton />
        </CardFooter>
      </Card>
    </div>
  )
}