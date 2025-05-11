import React from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { LoginCard } from 'src/components/login-card';
import { TermsDisclaimer } from 'src/components/terms-disclaimer';
import { ThemeToggle } from 'src/components/theme-toggle';

export const Route = createFileRoute('/login')({
	component: Login,
});

function Login() {
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
				<LoginCard />
				<TermsDisclaimer />
			</div>
		</div>
	);
}
