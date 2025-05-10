import { LoginForm } from '@/components/login-card';
import { TermsDisclaimer } from '@/components/terms-disclaimer';
import { ThemeToggle } from '@/components/theme-toggle';
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/login')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/login"!</div>
}

export function meta() {
	return [
		{ title: "Log in | Sealnext" },
		{ name: "description", content: "Log in to Sealnext to continue." },
	];
}

export default function Login() {
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
				<LoginForm />
				<TermsDisclaimer />
			</div>
		</div>
	);
}
