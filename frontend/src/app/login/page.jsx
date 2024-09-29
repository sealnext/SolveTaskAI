'use client'

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
      router.push('/dashboard')
    }
  }, [status, router])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setPending(true)

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
        router.push("/dashboard")
      }
    } catch (error) {
      console.error("Login error:", error)
      setErrorMessage("An error occurred during login")
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
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <h1 className="text-2xl font-semibold text-center">Welcome Back</h1>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <MailIcon
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                  size={18} />
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  className="pl-10"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <LockIcon
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                  size={18} />
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  className="pl-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(checked) => setRememberMe(checked)} />
                <Label
                  htmlFor="remember"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Remember me
                </Label>
              </div>
              <Button variant="link" className="text-sm text-primary p-0">
                Forgot password?
              </Button>
            </div>
            <Button type="submit" className="w-full" disabled={pending}>
              {pending ? 'Signing In...' : 'Sign In'}
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
          <p className="text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Button variant="link" className="p-0 text-primary">
              Sign up
            </Button>
          </p>
          <LoginStatusButton />
        </CardFooter>
      </Card>
    </div>
  )
}