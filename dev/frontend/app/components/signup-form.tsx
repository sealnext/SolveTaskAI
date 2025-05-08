import React, { useState } from 'react';
import { cn } from "~/lib/utils";
import { Button } from "~/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import { Form, Link } from "react-router";
import { Eye, EyeOff } from "lucide-react";

interface SignUpFormProps extends React.ComponentPropsWithoutRef<"div"> {
	error?: boolean;
	errorMessage?: string;
}

export function SignUpForm({
	error,
	errorMessage
}: SignUpFormProps) {

	const [showPassword, setShowPassword] = useState(false);

	return (
		<Card>
			<CardHeader className="text-center">
				<CardTitle className="text-xl">Create an account</CardTitle>
				<CardDescription>
					Sign up with an email and password
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Form method="post">
					<div className="grid gap-6">
						<div className="grid gap-6">
							{error && (
								<div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
									{errorMessage || "An error occurred during login. Please try again."}
								</div>
							)}
							<div className="grid gap-2">
								<Label htmlFor="email">Email</Label>
								<Input
									id="email"
									name="email"
									type="email"
									placeholder="andy@example.com"
									required
									className={cn(error && "border-destructive")}
								/>
							</div>
							<div className="grid gap-2">
								<div className="flex items-center">
									<Label htmlFor="password">Password</Label>
								</div>
								<div className="relative">
									<Input
										id="password"
										name="password"
										type={showPassword ? "text" : "password"}
										required
										className={cn(error && "border-destructive")}
									/>
									<button
										type="button"
										className="absolute right-0 top-0 h-full aspect-square rounded-full flex items-center justify-center group hover:cursor-pointer"
										onClick={() => setShowPassword(!showPassword)}
									>
										<span className="absolute inset-0 w-8 h-8 rounded-full bg-transparent group-hover:bg-black/5 m-auto" />
										{showPassword ? <EyeOff className="h-4 w-4 relative z-10" /> : <Eye className="h-4 w-4 relative z-10" />}
									</button>
								</div>
							</div>
							<Button type="submit" className="w-full hover:cursor-pointer">
								Sign up
							</Button>
						</div>
						<div className="text-center text-sm">
							Already have an account?{" "}
							<Link to="/login" className="underline underline-offset-4">
								Log in
							</Link>
						</div>
					</div>
				</Form>
			</CardContent>
		</Card>
	)
}
