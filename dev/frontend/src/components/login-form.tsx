import React, { useState } from 'react';
import { z } from 'zod';
import { useForm } from '@tanstack/react-form';
import { Link } from '@tanstack/react-router';
import { Eye, EyeOff } from 'lucide-react';
import { FaGithub, FaGoogle } from 'react-icons/fa';
import { useLogin } from 'src/lib/hook';
import { loginSchema } from 'src/lib/schema';
import { Button } from 'src/components/ui/button';
import { Input } from 'src/components/ui/input';
import { Label } from 'src/components/ui/label';
import { cn } from 'src/lib/utils';

export function LoginForm() {
	const { mutate: login } = useLogin();
	const [showPassword, setShowPassword] = useState(false);
	const [formError, setFormError] = useState<string | null>(null);

	const form = useForm({
		defaultValues: {
			email: '',
			password: '',
		},
		onSubmit: async ({ value }) => {
			try {
				setFormError(null);
				await login(value);
			} catch {
				setFormError('An error occurred during login. Please try again.');
			}
		},
	});

	return (
		<form
			onSubmit={(e) => {
				e.preventDefault();
				e.stopPropagation();
				form.handleSubmit();
			}}
		>
			<div className="grid gap-6">
				<div className="flex flex-col gap-4">
					<Button variant="outline" type="button" className="w-full hover:cursor-pointer">
						<FaGithub />
						Log in with GitHub
					</Button>
					<Button variant="outline" type="button" className="w-full hover:cursor-pointer">
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
					{formError && (
						<div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
							{formError}
						</div>
					)}
					<form.Field
						name="email"
						validators={{
							onChange: (field) => {
								try {
									z.string().email().parse(field.value);
									return undefined;
								} catch {
									if (field.value) {
										return 'Please enter a valid email address';
									}
									return 'Email is required';
								}
							}
						}}
					>
						{(field) => (
							<div className="grid gap-2">
								<Label htmlFor={field.name}>Email</Label>
								<Input
									id={field.name}
									name={field.name}
									type="email"
									placeholder="andy@example.com"
									value={field.state.value}
									onChange={(e) => field.handleChange(e.target.value)}
									onBlur={field.handleBlur}
									className={cn(field.state.meta.errors.length > 0 && 'border-destructive')}
								/>
								{field.state.meta.errors.length > 0 && (
									<div className="text-sm text-destructive">{field.state.meta.errors.join(', ')}</div>
								)}
							</div>
						)}
					</form.Field>
					
					<form.Field
						name="password"
						validators={{
							onChange: (field) => {
								try {
									loginSchema.shape.password.parse(field.value);
									return undefined;
								} catch {
									if (!field.value) {
										return 'Password is required';
									}
									return 'Password must be at least 12 characters with letters, numbers, and symbols';
								}
							}
						}}
					>
						{(field) => (
							<div className="grid gap-2">
								<div className="flex items-center">
									<Label htmlFor={field.name}>Password</Label>
									<a
										href="#"
										className="ml-auto text-sm underline-offset-4 hover:underline text-right"
									>
										Forgot your password?
									</a>
								</div>
								<div className="relative">
									<Input
										id={field.name}
										name={field.name}
										type={showPassword ? 'text' : 'password'}
										value={field.state.value}
										onChange={(e) => field.handleChange(e.target.value)}
										onBlur={field.handleBlur}
										className={cn(field.state.meta.errors.length > 0 && 'border-destructive')}
									/>
									<button
										type="button"
										className="absolute right-0 top-0 h-full aspect-square rounded-full flex items-center justify-center group hover:cursor-pointer"
										onClick={() => setShowPassword(!showPassword)}
									>
										<span className="absolute inset-0 w-8 h-8 rounded-full bg-transparent group-hover:bg-black/5 m-auto" />
										{showPassword ? (
											<EyeOff className="h-4 w-4 relative z-10" />
										) : (
											<Eye className="h-4 w-4 relative z-10" />
										)}
									</button>
								</div>
								{field.state.meta.errors.length > 0 && (
									<div className="text-sm text-destructive">{field.state.meta.errors.join(', ')}</div>
								)}
							</div>
						)}
					</form.Field>
					
					<form.Subscribe
						selector={(state) => [state.canSubmit, state.isSubmitting]}
					>
						{([canSubmit, isSubmitting]) => (
							<Button type="submit" disabled={!canSubmit} className="w-full hover:cursor-pointer">
								{isSubmitting ? 'Logging in...' : 'Log in'}
							</Button>
						)}
					</form.Subscribe>
				</div>
				<div className="text-center text-sm">
					Don&apos;t have an account?{' '}
					<Link to="/signup" className="underline underline-offset-4">
						Sign up
					</Link>
				</div>
			</div>
		</form>
	);
}
