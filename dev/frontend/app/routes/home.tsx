import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "SEALNEXT" },
    { name: "description", content: "AI for ticketing systems." },
  ];
}

export default function Home() {
  return (
    <div>
      <h1>Welcome</h1>
    </div>
  );
}
