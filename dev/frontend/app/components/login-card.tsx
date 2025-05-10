import React, { useState } from 'react';
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "@tanstack/react-router";
import { Eye, EyeOff } from "lucide-react";
import { FaGithub, FaGoogle } from "react-icons/fa";
import { useLogin } from '@/lib/hook';

interface LoginFormProps extends React.ComponentPropsWithoutRef<"div"> {
	error?: boolean;
	errorMessage?: string;
}

export function LoginForm({
	error,
	errorMessage,
}: LoginFormProps) {

	const { mutate: login } = useLogin();
	const [showPassword, setShowPassword] = useState(false);

	return (
		<Card>
			<CardHeader className="text-center">
				<CardTitle className="text-xl">Welcome back</CardTitle>
				<CardDescription>
					Use your GitHub or Google account
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Form method="post">
					<div className="grid gap-6">
						<div className="flex flex-col gap-4">
							<Button variant="outline" className="w-full hover:cursor-pointer">
								<FaGithub />
								Log in with GitHub
							</Button>
							<Button variant="outline" className="w-full hover:cursor-pointer">
								<FaGoogle />
								Log in with Google
							</Button>
						</div>
						<div className="relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t after:border-border">
							<span className="relative z-10 bg-card px-2 text-muted-foreground">
								Or continue with
							</span>
						</div>
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
									<a
										href="#"
										className="ml-auto text-sm underline-offset-4 hover:underline text-right"
									>
										Forgot your password?
									</a>
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
								Log in
							</Button>
						</div>
						<div className="text-center text-sm">
							Don&apos;t have an account?{" "}
							<Link to="/signup" className="underline underline-offset-4">
								Sign up
							</Link>
						</div>
					</div>
				</Form>
			</CardContent>
		</Card>
	)
}
