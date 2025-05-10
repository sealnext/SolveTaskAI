import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
	index("routes/main.tsx"),
	route("login", "routes/login.tsx"),
	route("signup", "routes/signup.tsx"),
	route("terms", "routes/terms.tsx"),
	route("privacy", "routes/privacy.tsx")
] satisfies RouteConfig;
