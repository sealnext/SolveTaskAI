import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuGroup,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
	Avatar,
	AvatarFallback,
} from "@/components/ui/avatar"
import { Form } from "react-router"
import {
	AlertCircle,
	Loader2,
	Menu as MenuIcon,
	User,
	Shield,
	Settings,
	Users,
	HelpCircle,
	LogOut
} from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

export function Menu() {

	const  { isPending, error, data } = useQuery({
		queryKey: ["user", "profile"],
		queryFn: () => fetch("/api/user/profile")
			.then(response => {
				if (!response.ok) {
					throw new Error(`${response.statusText}`);
				}
				return response.json();
			})
	});

	return (
		<TooltipProvider>
			<DropdownMenu>
				<DropdownMenuTrigger asChild>
					<Avatar className="ring-2 ring-offset-1 ring-blue-300 hover:ring-blue-400 hover:cursor-pointer data-[state=open]:ring-blue-500 w-10 h-10">
						<AvatarFallback className="leading-none">
							{data?.name?.charAt(0).toUpperCase() || data?.email?.charAt(0).toUpperCase() || <MenuIcon className="h-5 w-5" />}
						</AvatarFallback>
					</Avatar>
				</DropdownMenuTrigger>
				<DropdownMenuContent className={`mt-1 mr-4 ${isPending || error ? 'min-w-[190px]' : 'min-w-[150px]'}`}>
					<DropdownMenuLabel className="text-center">
						{isPending ? (
							<Tooltip>
								<TooltipTrigger asChild>
									<div className="flex items-center gap-2">
										<Loader2 className="h-5 w-5 animate-spin" />
										Loading...
									</div>
								</TooltipTrigger>
								<TooltipContent>
									<p>Fetching your name</p>
								</TooltipContent>
							</Tooltip>
						) : error ? (
							<Tooltip>
								<TooltipTrigger asChild>
									<div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-medium cursor-help">
										<AlertCircle className="h-5 w-5" />
										{error.message}
									</div>
								</TooltipTrigger>
								<TooltipContent>
									<p>Failed to fetch your name</p>
								</TooltipContent>
							</Tooltip>
						) : (
							data?.name || data?.email
						)}
					</DropdownMenuLabel>
					<DropdownMenuSeparator />
					<DropdownMenuGroup>
						<DropdownMenuItem className="cursor-pointer">
							<User className="h-4 w-4 mr-0" />
							Profile
						</DropdownMenuItem>
						<DropdownMenuItem className="cursor-pointer">
							<Shield className="h-4 w-4 mr-0" />
							Security
						</DropdownMenuItem>
						<DropdownMenuItem className="cursor-pointer">
							<Settings className="h-4 w-4 mr-0" />
							Settings
						</DropdownMenuItem>
						<DropdownMenuItem className="cursor-pointer">
							<Users className="h-4 w-4 mr-0" />
							Invite users
						</DropdownMenuItem>
						<DropdownMenuItem className="cursor-pointer">
							<HelpCircle className="h-4 w-4 mr-0" />
							Support
						</DropdownMenuItem>
					</DropdownMenuGroup>
					<DropdownMenuSeparator />
					<Form method="post" className="w-full h-full">
						<button type="submit" className="w-full h-full text-left flex items-center gap-2">
							<DropdownMenuItem onSelect={(e) => e.preventDefault()} className="cursor-pointer w-full h-full">
								<LogOut className="h-4 w-4" />
								Log out
							</DropdownMenuItem>
						</button>
					</Form>
				</DropdownMenuContent>
			</DropdownMenu>
		</TooltipProvider>
	)
}
