import React from 'react';
import type { Route } from "./+types/login";
import { GalleryVerticalEnd } from "lucide-react";
import { LoginForm } from "~/components/login-form";

export type LoginActionData = {
  error?: boolean;
  message?: string;
  [key: string]: unknown;
};

export async function clientAction({
  request,
}: Route.ClientActionArgs): Promise<LoginActionData> {
  const formData = await request.formData();
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });
  
  if (response.status === 500) {
    return { 
      error: true, 
      message: "Authentication failed. Please check your credentials."
    };
  }
  
  const responseData = await response.json();
  return responseData as LoginActionData;
}

export default function Login({
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
        <LoginForm error={actionData?.error} errorMessage={actionData?.message} />
      </div>
    </div>
	);
}
