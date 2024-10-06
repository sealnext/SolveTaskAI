"use client"

import { useState, useEffect } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"
import { LogoutButton } from "@/components/LogoutButton"
import { cn } from "@/lib/utils"
import { useSession } from "next-auth/react"
import { Moon, Sun } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import * as SwitchPrimitives from "@radix-ui/react-switch"
import { Command } from "lucide-react"
import { useTheme } from "@/contexts/ThemeContext"

const ThemeSwitch = ({ checked, onCheckedChange }) => (
  <SwitchPrimitives.Root
    checked={checked}
    onCheckedChange={onCheckedChange}
    className={cn(
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
      checked ? "bg-gray-700 dark:bg-gray-300" : "bg-gray-300 dark:bg-gray-600"
    )}
  >
    <SwitchPrimitives.Thumb className={cn(
      "pointer-events-none block h-5 w-5 rounded-full shadow-lg ring-0 transition-transform",
      checked ? "translate-x-5 bg-gray-800" : "translate-x-0 bg-white"
    )}>
      <div className="flex items-center justify-center h-full w-full">
        {checked ? (
          <Moon className="h-3 w-3 text-white" />
        ) : (
          <Sun className="h-3 w-3 text-gray-800" />
        )}
      </div>
    </SwitchPrimitives.Thumb>
  </SwitchPrimitives.Root>
)

const MenuItem = ({ icon: Icon, children, onClick, shortcut }) => (
  <button
    className="w-full text-left px-4 py-2 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-sm font-medium text-gray-700 dark:text-gray-200"
    onClick={onClick}
  >
    <div className="flex items-center">
      {Icon && <Icon className="mr-2 h-4 w-4 text-gray-500 dark:text-gray-400" />}
      <span>{children}</span>
    </div>
    {shortcut && (
      <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
        <Command className="h-3 w-3 mr-1" />
        S
      </span>
    )}
  </button>
)

export function ProfileMenuComponent() {
  const [isPremium, setIsPremium] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const { theme, toggleTheme } = useTheme()
  const { data: session } = useSession()
  const [isVisible, setIsVisible] = useState(false)

  const userName = session?.user?.full_name || session?.user?.name || "User"
  const userEmail = session?.user?.email || "email@example.com"
  const userImage = session?.user?.image || "/path/to/default/avatar.png"
  
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isOpen && !event.target.closest('[data-dropdown-content]')) {
        setIsOpen(false)
      }
    }

    const handleEscape = (event) => {
      if (isOpen && event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true)
    } else {
      const timer = setTimeout(() => setIsVisible(false), 200)
      return () => clearTimeout(timer)
    }
  }, [isOpen])

  return (
    <div className="relative">
      <Avatar 
        className="h-10 w-10 cursor-pointer bg-blue-500 text-white"
        onClick={() => setIsOpen(!isOpen)}
      >
        <AvatarImage src={userImage} alt={userName} />
        <AvatarFallback>{userName.charAt(0)}</AvatarFallback>
      </Avatar>
      {isVisible && (
        <div
          data-dropdown-content
          className={cn(
            "absolute right-0 mt-2 w-64 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 z-10 text-sm",
            "transition-opacity duration-200 ease-in-out",
            isOpen ? "opacity-100" : "opacity-0"
          )}
        >
          <div className="p-4">
            <p className="text-gray-700 dark:text-gray-200 font-medium">{userEmail}</p>
          </div>
          <Separator className="bg-gray-200 dark:bg-gray-700" />
          <div className="py-1">
            <MenuItem>Dashboard</MenuItem>
            <MenuItem>Billing</MenuItem>
            <MenuItem>Support</MenuItem>
          </div>
          <Separator className="bg-gray-200 dark:bg-gray-700" />
          <div className="px-4 py-2 flex justify-between items-center">
            <span className="text-gray-700 dark:text-gray-200 font-medium">Theme</span>
            <ThemeSwitch checked={theme === 'dark'} onCheckedChange={toggleTheme} />
          </div>
          <div className="py-1">
            <MenuItem shortcut="S">Account Settings</MenuItem>
          </div>
          <Separator className="bg-gray-200 dark:bg-gray-700" />
          <div className="p-2">
            <LogoutButton className="w-full justify-between text-left px-2 flex items-center hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-200 font-medium">
              {({ logout, isLoading }) => (
                <>
                  <span>{isLoading ? 'Logging out...' : 'Log out'}</span>
                  <LogOut className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                </>
              )}
            </LogoutButton>
          </div>
          <div className="p-2">
            <Button
              variant="default"
              size="sm"
              className="w-full rounded bg-gray-900 text-white hover:bg-gray-800 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100 font-medium"
              onClick={() => setIsPremium(true)}>
              Upgrade to Pro
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}