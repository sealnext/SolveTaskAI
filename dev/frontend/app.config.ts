import { defineConfig } from '@tanstack/react-start/config'
import tailwindcss from "@tailwindcss/vite";
import tsConfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
	vite: {
		plugins: [
			tailwindcss(),
			tsConfigPaths({
				projects: ['./tsconfig.json'],
			}),
		],
		server: {
			port: 80,
			proxy: {
				'/api': process.env.BACKEND_CONTAINER_URL || 'http://localhost:8000'
			}
		}
	},
})