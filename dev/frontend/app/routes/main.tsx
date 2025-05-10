
import { redirect } from 'react-router';
import { Menu } from "~/components/dropdown-menu";
import { ThemeToggle } from '~/components/theme-toggle';
import ChatContent from '~/components/chat-content';
import ChatSidebar from '~/components/chat-sidebar';
import { SidebarProvider, SidebarTrigger, SidebarInset } from "~/components/ui/sidebar"
import { PanelLeftIcon } from "lucide-react";
import { Button } from "~/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "~/components/ui/tooltip";

export function meta() {
	return [
		{ title: "Chat | Sealnext" },
		{ name: "description", content: "AI for ticketing systems." },
	];
}

export async function clientAction() {
	await fetch("/api/auth/logout", {
		method: "POST"
	});
	return redirect("/login");
}

export default function Home() {
	return (
		<SidebarProvider>
			<div className="relative flex flex-col h-full w-full">
				<div className="absolute top-3 right-6 z-10">
					<div className="flex items-center justify-center gap-4">
						<ThemeToggle />
						<Menu />
					</div>
				</div>
				<div className="flex-1 flex h-full w-full">
					<ChatSidebar />
							<SidebarTrigger className="ml-1 mt-2.5"/>
					<SidebarTrigger className="hidden" />
					<div className="flex-1">
						<ChatContent />
					</div>
				</div>
			</div>
		</SidebarProvider>	
	);
}
