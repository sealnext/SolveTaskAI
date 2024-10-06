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
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
      <Card className="w-full max-w-md bg-white dark:bg-gray-800 shadow-lg">
        <CardHeader>
          <h1 className="text-2xl font-semibold text-center text-gray-900 dark:text-gray-100">Welcome Back</h1>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-700 dark:text-gray-300">Email</Label>
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
              <Label htmlFor="password" className="text-gray-700 dark:text-gray-300">Password</Label>
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
                  className="border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:checked:bg-blue-500 dark:checked:border-blue-500" />
                <Label
                  htmlFor="remember"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-gray-700 dark:text-gray-300">
                  Remember me
                </Label>
              </div>
              <Button variant="link" className="text-sm text-primary p-0 dark:text-blue-400 hover:dark:text-blue-300">
                Forgot password?
              </Button>
            </div>
            <Button 
              type="submit" 
              className="w-full bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500 dark:hover:bg-blue-600" 
              disabled={pending}
            >
              {pending ? 'Connecting...' : 'Login'}
            </Button>
            {errorMessage && (
              <div className="flex items-center space-x-2 text-red-500">
                <AlertCircle size={18} />
                <p className="text-sm">{errorMessage}</p>
              </div>
            )}
          </form>
        </CardContent>
        <CardFooter className="justify-center flex-col">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Don't have an account?{' '}
            <Button variant="link" className="p-0 text-primary dark:text-blue-400" onClick={() => router.push('/signup')}>
              Sign up
            </Button>
          </p>
          <LoginStatusButton />
        </CardFooter>
      </Card>
    </div>
  )
}