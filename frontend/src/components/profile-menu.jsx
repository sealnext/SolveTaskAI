"use client"

import { useState } from "react"
import { AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { CreditCard, LogOut, Settings, Star, BarChart2, HelpCircle, XCircle } from "lucide-react"
import { LogoutButton } from "@/components/LogoutButton"
import { cn } from "@/lib/utils" // Utility function for conditional classes
import { useSession } from "next-auth/react"

export function ProfileMenuComponent() {
  const [isPremium, setIsPremium] = useState(false)
  const { data: session } = useSession()

  const userName = session?.user?.full_name || session?.user?.name || "User"
  const userEmail = session?.user?.email || "email@example.com"

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="flex flex-row items-center space-x-3 w-full px-4 py-3 rounded-lg hover:bg-gray-50 focus:bg-gray-100 transition-colors duration-200 outline-none"
        >
          <div className="flex flex-col items-start">
            <p className="text-sm font-semibold leading-none truncate max-w-[180px]">{userName}</p>
            <p className="text-xs leading-none text-muted-foreground truncate max-w-[180px]">{userEmail}</p>
          </div>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className={cn(
          "w-64 rounded-md shadow-lg border border-gray-200 bg-white",
          "data-[side=bottom]:translate-y-1",
          "data-[side=top]:translate-y-1"
        )}
        align="center"
        sideOffset={5}
        forceMount
      >
        <DropdownMenuSeparator />
        {!isPremium ? (
          <div className="px-4 py-1.5 text-sm cursor-default">
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
          <div className="px-4 py-1 text-sm text-muted-foreground cursor-default">
            <p className="text-xs">You are a Premium User</p>
          </div>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem>
            <CreditCard className="mr-2 h-4 w-4 text-primary" />
            <span>Billing</span>
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Settings className="mr-2 h-4 w-4 text-primary" />
            <span>Account Settings</span>
          </DropdownMenuItem>
          <DropdownMenuItem>
            <BarChart2 className="mr-2 h-4 w-4 text-primary" />
            <span>Analytics</span>
          </DropdownMenuItem>
          <DropdownMenuItem>
            <HelpCircle className="mr-2 h-4 w-4 text-primary" />
            <span>Help & Support</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <LogoutButton>
            <LogOut className="mr-2 h-4 w-4 text-red-500" />
            <span>Log out</span>
          </LogoutButton>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}