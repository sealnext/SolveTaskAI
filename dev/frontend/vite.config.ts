import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { TanStackRouterVite } from '@tanstack/router-plugin/vite'
import tailwindcss from '@tailwindcss/vite';
import tsConfigPaths from 'vite-tsconfig-paths';

// https://vitejs.dev/config/
export default defineConfig({
	server: {
		port: 80,
		proxy: {
			'/api': process.env.BACKEND_CONTAINER_URL || 'http://localhost:8000',
		},
	},
  plugins: [
    // Please make sure that '@tanstack/router-plugin' is passed before '@vitejs/plugin-react'
    TanStackRouterVite({ target: 'react', autoCodeSplitting: true }),
    react(),
		tailwindcss(),
		tsConfigPaths({
			projects: ['./tsconfig.json'],
		}),
  ],
})