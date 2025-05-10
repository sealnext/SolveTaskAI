import React from 'react';
import type { Route } from "./+types/signup";
import { SignUpForm } from '~/components/signup-form';
import { redirect } from 'react-router';
import { TermsDisclaimer } from '~/components/terms-disclaimer';
import { loginSchema, validatePassword } from '~/lib/zod';
import { useQuery } from '@tanstack/react-query';

export function meta() {
	return [
		{ title: "Sign up | Sealnext" },
		{ name: "description", content: "Sign up to Sealnext to continue." },
	];
}

export type SignUpActionData = {
  error?: boolean;
  message?: string;
  fieldErrors?: {
    email?: string;
    password?: string | string[];
  };
};

export async function clientAction({
  request,
}: Route.ClientActionArgs): Promise<SignUpActionData | Response> {

	const formData = await request.formData();
	const email = formData.get("email") as string;
	const password = formData.get("password") as string;

	const fieldErrors: SignUpActionData['fieldErrors'] = {};
	let hasErrors = false;

	const emailResult = loginSchema.shape.email.safeParse(email);
	if (!emailResult.success) {
		fieldErrors.email = emailResult.error.errors[0].message;
		hasErrors = true;
	}

	const passwordErrors = validatePassword(password);
	if (passwordErrors.length > 0) {
		fieldErrors.password = passwordErrors;
		hasErrors = true;
	}

	if (hasErrors) {
		return {
			error: true,
			message: "Please correct the errors below",
			fieldErrors
		};
	}

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

	const { data } = useQuery({
		queryKey: ["auth", "status"],
		queryFn: () => fetch("/api/auth/status")
			.then(response => {
				return response.ok;
			}),
		retry: false
	});

	if (data) {
		return redirect("/");
	}

  return (
		<div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted p-6 md:p-10">
			<div className="flex w-full max-w-sm flex-col gap-6">
				<img
					src="https://cdn.sealnext.com/logo-full.svg"
					alt="SEALNEXT"
					className="w-full px-4 pointer-events-none dark:invert"
				/>
				<SignUpForm
					error={actionData?.error}
					errorMessage={actionData?.message}
					fieldErrors={actionData?.fieldErrors}
				/>
				<TermsDisclaimer />
			</div>
		</div>
  );
}