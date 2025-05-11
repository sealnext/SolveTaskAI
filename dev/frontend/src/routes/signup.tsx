import React from 'react';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/signup')({
	component: RouteComponent,
});

function RouteComponent() {
	return <div>Hello &quot;signup&quot;!</div>;
}
