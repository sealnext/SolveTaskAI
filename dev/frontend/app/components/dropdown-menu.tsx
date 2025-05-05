import React from "react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu"
import {
  Avatar,
  AvatarFallback,
} from "~/components/ui/avatar"
import { Form } from "react-router"

export function Menu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
				<Avatar className="ring-2 ring-offset-1 ring-blue-300 hover:ring-blue-400 data-[state=open]:ring-blue-500 w-10 h-10">
					<AvatarFallback>CN</AvatarFallback>
				</Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-40 mt-1 mr-4">
        <DropdownMenuLabel>My Account</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem>Profile</DropdownMenuItem>
          <DropdownMenuItem>Settings</DropdownMenuItem>
          <DropdownMenuItem>Invite users via email</DropdownMenuItem>
          <DropdownMenuItem>Support</DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
          <Form method="post" className="w-full h-full">
            <button type="submit" className="w-full h-full text-left">Log out</button>
          </Form>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
