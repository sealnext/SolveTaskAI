import React, { useEffect, useState } from 'react';
import {
	isRouteErrorResponse,
	Links,
	Meta,
	Outlet,
	Scripts,
	ScrollRestoration,
} from "react-router";

import type { Route } from "./+types/root";
import "./app.css";

import { useAtomValue } from 'jotai'
import { themeAtom } from '~/lib/atom'

export function Layout({ children }: { children: React.ReactNode }) {
	const theme = useAtomValue(themeAtom);
	const [isDarkMode, setIsDarkMode] = useState(false);

	useEffect(() => {
		if (theme === 'system') {
			const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
			setIsDarkMode(mediaQuery.matches);

			const handleChange = () => setIsDarkMode(mediaQuery.matches);
			mediaQuery.addEventListener('change', handleChange);

			return () => mediaQuery.removeEventListener('change', handleChange);
		} else {
			setIsDarkMode(theme === 'dark');
		}
	}, [theme]);

	return (
		<html lang="en" className={`w-full h-full ${isDarkMode ? 'dark' : ''}`}>
			<head>
				<meta charSet="utf-8" />
				<meta name="viewport" content="width=device-width, initial-scale=1" />

				<link rel="icon" type="image/svg+xml" href="http://cdn.sealnext.com/favicon.svg" media="(prefers-color-scheme: light)" />
				<link rel="icon" type="image/svg+xml" href="http://cdn.sealnext.com/favicon-white.svg" media="(prefers-color-scheme: dark)" />

				<link rel="icon" type="image/png" href="http://cdn.sealnext.com/favicon-96x96.png" sizes="96x96" media="(prefers-color-scheme: light)" />
				<link rel="icon" type="image/png" href="http://cdn.sealnext.com/favicon-white-96x96.png" sizes="96x96" media="(prefers-color-scheme: dark)" />

				<link rel="icon" href="http://cdn.sealnext.com/favicon.ico" media="(prefers-color-scheme: light)" />
				<link rel="icon" href="http://cdn.sealnext.com/favicon-white.ico" media="(prefers-color-scheme: dark)" />

				<meta name="apple-mobile-web-app-title" content="SEALNEXT" />
				<link rel="apple-touch-icon" sizes="180x180" href="http://cdn.sealnext.com/apple-touch-icon.png" />

				<link rel="manifest" href="/manifest.json" />

				<Meta />
				<Links />
			</head>
			<body className="w-full h-full">
				{children}
				<ScrollRestoration />
				<Scripts />
			</body>
		</html>
	);
}

export default function App() {
	return <Outlet />;
}

// export function HydrateFallback() {
// 	return (
// 		<div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted p-6 md:p-10">
// 			<div className="flex w-full max-w-sm flex-col gap-6">
// 				<img src="https://cdn.sealnext.com/logo-full.svg" alt="Sealnext" className="w-full px-4" />
// 			</div>
// 		</div>
// 	);
// }

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
	let message = "Oops!";
	let details = "An unexpected error occurred.";
	let stack: string | undefined;

	if (isRouteErrorResponse(error)) {
		message = error.status === 404 ? "404" : "Error";
		details =
			error.status === 404
				? "The requested page could not be found."
				: error.statusText || details;
	} else if (import.meta.env.DEV && error && error instanceof Error) {
		details = error.message;
		stack = error.stack;
	}

	return (
		<main className="pt-16 p-4 container mx-auto">
			<h1>{message}</h1>
			<p>{details}</p>
			{stack && (
				<pre className="w-full p-4 overflow-x-auto">
					<code>{stack}</code>
				</pre>
			)}
		</main>
	);
}
