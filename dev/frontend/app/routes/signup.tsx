import React from 'react';
import type { Route } from "./+types/signup";

import { GalleryVerticalEnd } from 'lucide-react';
import { SignUpForm } from '~/components/signup-form';
import { redirect } from 'react-router';

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
				message: "Sign up failed. Probably email is already in use or password is too weak."
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
				<a href="#" className="flex items-center gap-2 self-center font-medium">
					<div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
						<GalleryVerticalEnd className="size-4" />
					</div>
					SEALNEXT
				</a>
				<SignUpForm error={actionData?.error} errorMessage={actionData?.message} />
			</div>
		</div>
  );
}