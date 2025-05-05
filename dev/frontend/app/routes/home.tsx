import React from 'react';
import { redirect } from 'react-router';
import { Menu } from "~/components/dropdown-menu";
import { ThemeToggle } from '~/components/theme-toggle';

export function meta() {
	return [
		{ title: "Chat | Sealnext" },
		{ name: "description", content: "AI for ticketing systems." },
	];
}

export async function clientAction(): Promise<void | Response> {
	console.log("Logging out");
	const response = await fetch("/api/auth/logout", {
		method: "POST"
	});

	if (!response.ok) {
		throw new Error("Failed to logout");
	}

	console.log("Logged out");
	return redirect("/login");
}

export default function Home() {
	return (
		<div className="relative flex flex-col items-center justify-center h-full w-full">
			<div className="absolute top-3 right-6">
				<div className="flex items-center justify-center gap-4">
					<ThemeToggle />
					<Menu />
				</div>
			</div>
			<h1>Welcome</h1>
		</div>
	);
}
