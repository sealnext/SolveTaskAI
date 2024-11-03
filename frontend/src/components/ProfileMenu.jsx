"use client"

import { useState, useEffect } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { LogOut, Moon, Sun, Command, ChevronRight, User, CreditCard, LifeBuoy, Settings } from "lucide-react"
import { LogoutButton } from "@/components/LogoutButton"
import { cn } from "@/lib/utils"
import { useSession } from "next-auth/react"
import { Separator } from "@/components/ui/separator"
import * as SwitchPrimitives from "@radix-ui/react-switch"
import { useTheme } from "@/contexts/ThemeContext"
import { useRouter } from 'next/navigation'
import { SettingsDialog } from '@/components/SettingsDialog'

export const ThemeSwitch = ({ checked, onCheckedChange }) => (
  <SwitchPrimitives.Root
    checked={checked}
    onCheckedChange={onCheckedChange}
    className={cn(
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
      checked ? "bg-primary" : "bg-muted"
    )}
  >
    <SwitchPrimitives.Thumb className={cn(
      "pointer-events-none flex items-center justify-center h-5 w-5 rounded-full shadow-lg ring-0",
      checked ? "translate-x-5 bg-white" : "translate-x-0 bg-white"
    )}>
      {checked ? (
        <Moon className="h-3 w-3 text-primary" />
      ) : (
        <Sun className="h-3 w-3 text-primary" />
      )}
    </SwitchPrimitives.Thumb>
  </SwitchPrimitives.Root>
)

const MenuItem = ({ icon: Icon, children, onClick, shortcut }) => {
  return (
    <button
      className="w-full text-left px-4 py-3 flex items-center justify-between hover:bg-muted-20 active:bg-muted transition-colors text-sm font-medium text-foreground rounded-lg cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center">
        {Icon && <Icon className="mr-3 h-4 w-4 text-primary" />}
        <span>{children}</span>
      </div>
      {shortcut ? (
        <span className="text-xs text-muted-foreground flex items-center">
          <Command className="h-3 w-3 mr-1" />
          {shortcut}
        </span>
      ) : (
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      )}
    </button>
  );
};

export function ProfileMenuComponent() {
  const [isPremium, setIsPremium] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
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
        className="h-10 w-10 cursor-pointer bg-primary text-foreground ring-2 ring-offset-2 ring-offset-background ring-primary transition-all hover:ring-secondary"
        onClick={() => setIsOpen(!isOpen)}
      >
        <AvatarImage src={userImage} alt={userName} />
        <AvatarFallback>{userName.charAt(0)}</AvatarFallback>
      </Avatar>
      {isVisible && (
        <div
          data-dropdown-content
          className={cn(
            "absolute right-0 mt-3 w-72 rounded-xl shadow-lg border border-muted bg-backgroundSecondary z-10 text-sm overflow-hidden",
            "transition-all duration-200 ease-in-out",
            isOpen ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
          )}
        >
          <div className="p-4 bg-primary/10">
            <p className="text-foreground font-semibold">{userName}</p>
            <p className="text-muted-foreground text-xs mt-1">{userEmail}</p>
          </div>
          <div className="p-2 space-y-1">
            <MenuItem icon={User}>Dashboard</MenuItem>
            <MenuItem icon={CreditCard}>Billing</MenuItem>
            <MenuItem icon={LifeBuoy}>Support</MenuItem>
          </div>
          <Separator className="my-2 bg-muted" />
          <div className="px-4 py-3 flex justify-between items-center">
            <span className="text-foreground font-medium">Dark Mode</span>
            <ThemeSwitch checked={theme === 'dark'} onCheckedChange={toggleTheme} />
          </div>
          <div className="p-2 space-y-1">
            <MenuItem 
              icon={Settings} 
              shortcut="S" 
              onClick={() => {
                setIsSettingsOpen(true);
                setIsOpen(false);
              }}
            >
              Account Settings
            </MenuItem>
          </div>
          <Separator className="my-2 bg-muted" />
          <div className="p-2">
            <LogoutButton className="w-full justify-between text-left px-4 py-3 flex items-center hover:bg-muted-20 transition-colors text-foreground font-medium rounded-lg">
              {({ logout, isLoading }) => (
                <>
                  <span className="flex items-center">
                    <LogOut className="h-4 w-4 mr-3 text-primary" />
                    {isLoading ? 'Logging out...' : 'Log out'}
                  </span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </>
              )}
            </LogoutButton>
          </div>
          <Separator className="my-2 bg-muted" />
          <div className="p-2">
            <Button
              variant="default"
              size="sm"
              className="w-full rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-medium py-3 cursor-pointer"
              onClick={() => setIsPremium(true)}>
              Upgrade to Pro
            </Button>
          </div>
        </div>
      )}

      <SettingsDialog 
        open={isSettingsOpen} 
        onOpenChange={setIsSettingsOpen}
      />
    </div>
  )
}