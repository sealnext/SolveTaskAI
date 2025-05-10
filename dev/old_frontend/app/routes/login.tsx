import React from 'react';
import type { Route } from "./+types/login";
import { LoginForm } from "~/components/login-form";
import { redirect } from 'react-router';
import { ThemeToggle } from '~/components/theme-toggle';
import { TermsDisclaimer } from '~/components/terms-disclaimer';
import { useLogin } from '~/lib/hook';

export function meta() {
	return [
		{ title: "Log in | Sealnext" },
		{ name: "description", content: "Log in to Sealnext to continue." },
	];
}

export default function Login({
	actionData,
}: Route.ComponentProps) {

	const { mutate: login } = useLogin();

	return (
		<div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted p-6 md:p-10">
			<div className="absolute top-3 right-6">
				<ThemeToggle />
			</div>
			<div className="flex w-full max-w-sm flex-col gap-6">
				<img
					src="https://cdn.sealnext.com/logo-full.svg"
					alt="SEALNEXT"
					className="w-full px-4 pointer-events-none dark:invert"
				/>
				<LoginForm error={actionData?.error} errorMessage={actionData?.message} />
				<TermsDisclaimer />
			</div>
		</div>
	);
}
