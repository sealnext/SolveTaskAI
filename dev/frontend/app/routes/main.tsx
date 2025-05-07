import React from 'react';
import { redirect } from 'react-router';
import { Menu } from "~/components/dropdown-menu";
import { ThemeToggle } from '~/components/theme-toggle';
import { useSetAtom } from 'jotai';
import { userNameAtom, userEmailAtom, userIsEmailVerifiedAtom } from '~/lib/atom';

export function meta() {
	return [
		{ title: "Chat | Sealnext" },
		{ name: "description", content: "AI for ticketing systems." },
	];
}

export async function clientLoader(): Promise<void | Response> {
	const setUserName = useSetAtom(userNameAtom);
	const setUserEmail = useSetAtom(userEmailAtom);
	const setUserIsEmailVerified = useSetAtom(userIsEmailVerifiedAtom);

	const response = await fetch("/api/user/profile", {
		method: "GET"
	});
	if (!response.ok) {
		if (response.status === 401) {
			return redirect("/login");
		}
		setUserName(null);
		setUserEmail(null);
		setUserIsEmailVerified(false);
	}

	const user = await response.json();

	setUserName(user.name);
	setUserEmail(user.email);
	setUserIsEmailVerified(user.isEmailVerified);
}

export async function clientAction(): Promise<void | Response> {
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
