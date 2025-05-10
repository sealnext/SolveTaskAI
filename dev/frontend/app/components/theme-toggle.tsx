import { Moon, Sun, Monitor, Check } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { themeAtom } from "@/lib/atom"
import { useAtom } from "jotai"

export function ThemeToggle() {
	const [theme, setTheme] = useAtom(themeAtom);

	return (
		<DropdownMenu>
			<DropdownMenuTrigger asChild>
				<Button variant="outline" size="icon" className="hover:cursor-pointer">
					<Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
					<Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
					<span className="sr-only">Toggle theme</span>
				</Button>
			</DropdownMenuTrigger>
			<DropdownMenuContent align="end" onCloseAutoFocus={(e) => e.preventDefault()}>
				<DropdownMenuItem
					onClick={() => setTheme("light")}
					className={`${theme === "light" && "bg-accent"} hover:cursor-pointer`}
				>
					<Sun className="mr-2 h-4 w-4" />
					<span>Light</span>
					{theme === "light" && <Check className="ml-auto h-4 w-4" />}
				</DropdownMenuItem>
				<DropdownMenuItem
					onClick={() => setTheme("dark")}
					className={`${theme === "dark" && "bg-accent"} hover:cursor-pointer`}
				>
					<Moon className="mr-2 h-4 w-4" />
					<span>Dark</span>
					{theme === "dark" && <Check className="ml-auto h-4 w-4" />}
				</DropdownMenuItem>
				<DropdownMenuItem
					onClick={() => setTheme("system")}
					className={`${theme === "system" && "bg-accent"} hover:cursor-pointer`}
				>
					<Monitor className="mr-2 h-4 w-4" />
					<span>System</span>
					{theme === "system" && <Check className="ml-auto h-4 w-4" />}
				</DropdownMenuItem>
			</DropdownMenuContent>
		</DropdownMenu>
	)
}
