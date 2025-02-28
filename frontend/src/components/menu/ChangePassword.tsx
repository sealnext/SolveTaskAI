'use client'

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import ApiClient from "@/lib/apiClient"
import { useState } from "react"

export function ChangePasswordDialog() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) {
      setMessage('Both passwords are required')
      return
    }

    setIsLoading(true)
    try {
      const apiClient = ApiClient()
      await apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      })
      setMessage('Password changed successfully')
      setCurrentPassword('')
      setNewPassword('')
    } catch (error) {
      setMessage('Error changing password. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <DialogContent className="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Change Password</DialogTitle>
        <DialogDescription>
          Enter your current password and a new password below.
        </DialogDescription>
      </DialogHeader>
      <div className="grid gap-4 py-4">
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor="current-password" className="text-right">
            Current
          </Label>
          <Input
            id="current-password"
            type="password"
            className="col-span-3"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor="new-password" className="text-right">
            New
          </Label>
          <Input
            id="new-password"
            type="password"
            className="col-span-3"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </div>
        {message && (
          <div className={`text-sm ${message.includes('Error') ? 'text-red-500' : 'text-green-500'}`}>
            {message}
          </div>
        )}
      </div>
      <DialogFooter>
        <Button
          onClick={handleChangePassword}
          disabled={isLoading}
        >
          {isLoading ? 'Changing...' : 'Change Password'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}
