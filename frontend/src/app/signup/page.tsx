'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { LockIcon, MailIcon, UserIcon, AlertCircle } from 'lucide-react'
import ApiClient from '@/lib/apiClient'
import { signIn } from 'next-auth/react'
export default function SignupPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [agreeTerms, setAgreeTerms] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const [pending, setPending] = useState(false)
  const router = useRouter()
  const { data: session, status } = useSession()
  const [errors, setErrors] = useState({})
  const apiClient = ApiClient()

  useEffect(() => {
    if (status === 'authenticated') {
      router.push('/chat')
    }
  }, [status, router])

  const validateForm = () => {
    const newErrors = {}

    if (name.length < 3 || name.length > 50 || !/^[a-zA-Z0-9]+$/.test(name)) {
      newErrors.name = 'Username must be alphanumeric and between 3-50 characters'
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Invalid email format'
    }

    if (password.length < 8 || password.length > 128) {
      newErrors.password = 'Password must be between 8-128 characters'
    }

    if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password) || !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, digit, and special character'
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setPending(true)
    setErrorMessage(null)

    if (!validateForm()) {
      setPending(false)
      return
    }

    try {
      const response = await apiClient.post('/auth/signup', {
        username: name,
        email,
        password
      })

      if (response.data.message === "User created successfully") {
        const loginRes = await signIn('credentials', {
          redirect: false,
          username: email,
          password,
        })

        if (loginRes?.error) {
          setErrorMessage("Signup successful, but couldn't log in automatically. Please log in.")
        } else {
          router.push("/chat")
        }
      }
    } catch (error) {
      console.error("Signup error:", error)
      setErrorMessage(error.message || "An error occurred during signup")
    } finally {
      setPending(false)
    }
  }

  if (status === 'loading' || status === 'authenticated') {
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md bg-backgroundSecondary shadow-lg border-none">
        <CardHeader>
          <h1 className="text-2xl font-semibold text-center text-foreground">Create an Account</h1>
          <p className="text-center text-muted-foreground mt-2">Please fill in your details to sign up.</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-foreground-secondary">Full Name</Label>
              <Input
                id="name"
                type="text"
                icon={UserIcon}
                placeholder="Enter your full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              {errors.name && <p className="text-red-500 text-sm">{errors.name}</p>}
            </div>
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
              {errors.email && <p className="text-red-500 text-sm">{errors.email}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-foreground-secondary">Password</Label>
              <Input
                id="password"
                type="password"
                icon={LockIcon}
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              {errors.password && <p className="text-red-500 text-sm">{errors.password}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-foreground-secondary">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                icon={LockIcon}
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
              {errors.confirmPassword && <p className="text-red-500 text-sm">{errors.confirmPassword}</p>}
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="terms"
                checked={agreeTerms}
                onCheckedChange={(checked) => setAgreeTerms(checked)}
                required
                className="border-muted bg-background-secondary checked:bg-primary"
              />
              <Label htmlFor="terms" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-foreground-secondary">
                I agree to the{' '}
                <Button variant="link" className="p-0 text-primary hover:text-secondary">
                  Terms of Service
                </Button>{' '}
                and{' '}
                <Button variant="link" className="p-0 text-primary hover:text-secondary">
                  Privacy Policy
                </Button>
              </Label>
            </div>
            <Button
              type="submit"
              className="w-full bg-primary hover:bg-secondary text-foreground"
              disabled={pending}
            >
              {pending ? 'Signing Up...' : 'Sign Up'}
            </Button>
            {errorMessage && (
              <div className="flex items-center space-x-2 text-accent">
                <AlertCircle size={18} />
                <p className="text-sm">{errorMessage}</p>
              </div>
            )}
          </form>
        </CardContent>
        <CardFooter className="justify-center">
          <p className="text-sm text-foreground-secondary">
            Already have an account?{' '}
            <Button variant="link" className="p-0 text-primary hover:text-secondary" onClick={() => router.push('/login')}>
              Sign in
            </Button>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
