"use client"

import { useState } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { CreditCard, LogOut, Settings, Star } from "lucide-react"
import { LogoutButton } from "@/components/LogoutButton"

export function ProfileMenuComponent() {
  const [isPremium, setIsPremium] = useState(false)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button 
          className="flex items-center space-x-3 px-4 py-2 rounded-full hover:bg-gray-100 focus:bg-gray-200 transition-colors duration-200 outline-none"
        >
          <Avatar className="h-8 w-8">
            <AvatarImage src="/placeholder.svg?height=32&width=32" alt="@username" />
            <AvatarFallback>UN</AvatarFallback>
          </Avatar>
          <div className="flex flex-col items-start">
            <p className="text-sm font-medium leading-none">Username</p>
            <p className="text-xs leading-none text-muted-foreground">user@example.com</p>
          </div>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        {!isPremium && (
          <>
            <DropdownMenuItem className="flex-col items-start">
              <p className="text-xs text-muted-foreground">Running out of messages?</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={() => setIsPremium(true)}>
                <Star className="mr-2 h-4 w-4 text-yellow-400" />
                Upgrade to Premium
              </Button>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
          </>
        )}
        <DropdownMenuGroup>
          <DropdownMenuItem>
            <CreditCard className="mr-2 h-4 w-4" />
            <span>Billing</span>
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Settings className="mr-2 h-4 w-4" />
            <span>Pricing</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <LogoutButton>
            <LogOut className="mr-2 h-4 w-4" />
            <span>Log out</span>
          </LogoutButton>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}