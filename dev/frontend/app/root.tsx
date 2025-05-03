import React from 'react';
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

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />

        <link rel="icon" type="image/svg+xml" href="https://cdn.sealnext.com/favicon.svg" media="(prefers-color-scheme: light)" />
        <link rel="icon" type="image/svg+xml" href="https://cdn.sealnext.com/favicon-white.svg" media="(prefers-color-scheme: dark)" />

        <link rel="icon" type="image/png" href="https://cdn.sealnext.com/favicon-96x96.png" sizes="96x96" media="(prefers-color-scheme: light)" />
        <link rel="icon" type="image/png" href="https://cdn.sealnext.com/favicon-white-96x96.png" sizes="96x96" media="(prefers-color-scheme: dark)" />

        <link rel="icon" href="https://cdn.sealnext.com/favicon.ico" media="(prefers-color-scheme: light)" />
        <link rel="icon" href="https://cdn.sealnext.com/favicon-white.ico" media="(prefers-color-scheme: dark)" />

        <meta name="apple-mobile-web-app-title" content="SEALNEXT" />
        <link rel="apple-touch-icon" sizes="180x180" href="https://cdn.sealnext.com/apple-touch-icon.png" />

        <link rel="manifest" href="/manifest.json" />

        <Meta />
        <Links />
      </head>
      <body>
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
