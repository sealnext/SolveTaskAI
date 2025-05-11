import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from 'src/components/ui/card';
import { LoginForm } from 'src/components/login-form';

export function LoginCard() {
	return (
		<Card>
			<CardHeader className="text-center">
				<CardTitle className="text-xl">Welcome back</CardTitle>
				<CardDescription>Use your GitHub or Google account</CardDescription>
			</CardHeader>
			<CardContent>
				<LoginForm />
			</CardContent>
		</Card>
	);
}
