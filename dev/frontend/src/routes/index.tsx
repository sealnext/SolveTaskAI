import React from 'react';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold">Welcome to SealNext</h1>
      <p>This is the home page</p>
    </div>
  );
}
