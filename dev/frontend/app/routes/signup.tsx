import React from 'react';
import type { Route } from "./+types/signup";

import { SignUpForm } from '~/components/signup-form';
import { redirect } from 'react-router';
import { TermsDisclaimer } from '~/components/terms-disclaimer';
export function meta() {
	return [
		{ title: "Sign up | Sealnext" },
		{ name: "description", content: "Sign up to Sealnext to continue." },
	];
}

export async function clientLoader(): Promise<void | Response> {
	const response = await fetch("/api/auth/verify");
	if (response.ok) {
		return redirect("/");
	}
}

export type SignUpActionData = {
  error?: boolean;
  message?: string;
};

export async function clientAction({
  request,
}: Route.ClientActionArgs): Promise<SignUpActionData | Response> {

	const formData = await request.formData();
	const email = formData.get("email") as string;
	const password = formData.get("password") as string;

	const response = await fetch("/api/auth/signup", {
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
				message: "Sign up failed. Possible reasons: email is already in use or password is too weak or an unexpected error occurred."
			};
		}
		return {
			error: true,
			message: "An unexpected error occurred during sign up. Please try again."
		};
	}

	return redirect("/");
}

export default function SignUp({
  actionData,
}: Route.ComponentProps) {
  return (
		<div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted p-6 md:p-10">
			<div className="flex w-full max-w-sm flex-col gap-6">
				<img
					src="https://cdn.sealnext.com/logo-full.svg"
					alt="Sealnext"
					className="w-full px-4 pointer-events-none dark:invert"
				/>
				<SignUpForm error={actionData?.error} errorMessage={actionData?.message} />
				<TermsDisclaimer />
			</div>
		</div>
  );
}