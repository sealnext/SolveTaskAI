"use client"

import { useState, useEffect } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { CreditCard, LogOut, Settings, Star, BarChart2, HelpCircle } from "lucide-react"
import { LogoutButton } from "@/components/LogoutButton"
import { cn } from "@/lib/utils"
import { useSession } from "next-auth/react"

// Definim o constantă pentru culoarea Avatar-ului
const AVATAR_BG_COLOR = "#2f394f"

export function ProfileMenuComponent() {
  const [isPremium, setIsPremium] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const { data: session } = useSession()

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

  const MenuItem = ({ icon: Icon, children, onClick }) => (
    <button
      className="w-full text-left px-4 py-2 flex items-center hover:bg-gray-100 transition-colors"
      onClick={onClick}
    >
      {Icon && <Icon className="mr-2 h-4 w-4 text-primary" />}
      <span>{children}</span>
    </button>
  )

  return (
    <div className="relative">
      <Avatar 
        className="h-10 w-10 cursor-pointer"
        bgColor={AVATAR_BG_COLOR}
        onClick={() => setIsOpen(!isOpen)}
      >
        <AvatarImage src={userImage} alt={userName} />
        <AvatarFallback textColor="white">{userName.charAt(0)}</AvatarFallback>
      </Avatar>
      {isOpen && (
        <div
          data-dropdown-content
          className={cn(
            "absolute right-0 mt-2 w-64 rounded-md shadow-lg border border-gray-200 bg-white",
            "z-10"
          )}
        >
          <div className={cn("flex items-center p-4", !isPremium && "border-b border-gray-200")}>
            <Avatar className="h-10 w-10 mr-3" bgColor={AVATAR_BG_COLOR}>
              <AvatarImage src={userImage} alt={userName} />
              <AvatarFallback textColor="white">{userName.charAt(0)}</AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-semibold">{userName}</p>
              <p className="text-xs text-gray-500">{userEmail}</p>
            </div>
          </div>
          <div className="py-1 px-4">
            {!isPremium ? (
              <div className="text-sm cursor-default">
                <p className="text-xs text-muted-foreground">Running out of messages?</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-1 w-full"
                  onClick={() => setIsPremium(true)}>
                  <Star className="mr-2 h-4 w-4 text-yellow-400" />
                  Upgrade to Premium
                </Button>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground cursor-default">
                <p className="text-xs">Premium account</p>
              </div>
            )}
          </div>
          <div className="border-t border-gray-200 pt-1">
            <MenuItem icon={CreditCard}>Billing</MenuItem>
            <MenuItem icon={Settings}>Account Settings</MenuItem>
            <MenuItem icon={BarChart2}>Analytics</MenuItem>
            <MenuItem icon={HelpCircle}>Help & Support</MenuItem>
          </div>
          <div className="border-t border-gray-200 mt-1 pl-1 pt-1 pb-1">
            <LogoutButton className="w-full text-left px-4 py-2 flex items-center hover:bg-gray-100 transition-colors">
              <LogOut className="mr-2 h-4 w-4 text-red-500" />
              <span>Log out</span>
            </LogoutButton>
          </div>
        </div>
      )}
    </div>
  )
}