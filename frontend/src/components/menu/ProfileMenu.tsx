'use client'

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ChangePasswordDialog } from "./ChangePassword"
import { Dialog, DialogTrigger } from "@/components/ui/dialog"
import ApiClient from "@/lib/apiClient"
import { signOut } from "next-auth/react"

export function ProfileMenuComponent() {
  const [dialogMenu, setDialogMenu] = useState<string>("none");
  const router = useRouter()
  const apiClient = ApiClient()

  const handleLogout = async () => {
    try {
      await apiClient.post('/auth/logout', {});
      await signOut({ redirect: false });
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }

  const handleDialogMenu = (): React.ReactElement | null => {
    switch (dialogMenu) {
      case "change-password":
        return <ChangePasswordDialog />
      default:
        return null;
    }
  };

  return (
    <Dialog>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Avatar className="ring-2 ring-primary ring-offset-2 ring-offset-background">
            <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
            <AvatarFallback>CN</AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56 mt-1 mr-1">
          <DropdownMenuLabel>Settings Menu</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>Security</DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <DialogTrigger asChild>
                  <DropdownMenuItem onSelect={() => setDialogMenu("change-password")}>
                    Change Password
                  </DropdownMenuItem>
                </DialogTrigger>
                <DropdownMenuItem>Two-Factor Auth</DropdownMenuItem>
                <DropdownMenuItem>Device History</DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuItem>Billing</DropdownMenuItem>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={handleLogout}>
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      {handleDialogMenu()}
    </Dialog>
  )
}