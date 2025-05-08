import React from 'react';
import { useSetAtom } from 'jotai';
import { redirect, useLoaderData } from 'react-router';
import { Menu } from "~/components/dropdown-menu";
import { ThemeToggle } from '~/components/theme-toggle';
import { userSchema } from '~/lib/zod';

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
