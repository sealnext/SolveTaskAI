import React from 'react';
import type { Route } from "./+types/login";
import { LoginForm } from "~/components/login-form";
import { redirect } from 'react-router';
import { ThemeToggle } from '~/components/theme-toggle';
import { TermsDisclaimer } from '~/components/terms-disclaimer';
export function meta() {
	return [
		{ title: "Log in | Sealnext" },
		{ name: "description", content: "Log in to Sealnext to continue." },
	];
}

export type LoginActionData = {
	error?: boolean;
	message?: string;
	[key: string]: unknown;
};

export async function clientLoader(): Promise<void | Response> {
	const response = await fetch("/api/auth/verify");
	if (response.ok) {
		return redirect("/");
	}
}

export async function clientAction({
	request,
}: Route.ClientActionArgs): Promise<LoginActionData | Response> {

	const formData = await request.formData();
	const email = formData.get("email") as string;
	const password = formData.get("password") as string;

	const response = await fetch("/api/auth/login", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ email, password }),
	});

	if (!response.ok) {
		if (response.status === 500) {
			return {
				error: true,
				message: "Authentication failed. Please check your credentials."
			};
		}
		else if (response.status === 422) {
			return {
				error: true,
				message: "Invalid credentials. Please check your email and password."
			};
		}
		return {
			error: true,
			message: "An unexpected error occurred during sign up. Please try again."
		};
	}

	return redirect("/");
}

export default function Login({
	actionData,
}: Route.ComponentProps) {
	return (
		<div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted p-6 md:p-10">
			<div className="absolute top-3 right-6">
				<ThemeToggle />
			</div>
			<div className="flex w-full max-w-sm flex-col gap-6">
				<img
					src="https://cdn.sealnext.com/logo-full.svg"
					alt="Sealnext"
					className="w-full px-4 pointer-events-none dark:invert"
				/>
				<LoginForm error={actionData?.error} errorMessage={actionData?.message} />
				<TermsDisclaimer />
			</div>
		</div>
	);
}
