/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			background: 'var(--color-background)',
  			foreground: 'var(--color-foreground)',
  			backgroundSecondary: 'var(--color-background-secondary)',
  			foregroundSecondary: 'var(--color-foreground-secondary)',
  			card: {
  				DEFAULT: 'var(--color-card)',
  				foreground: 'var(--color-card-foreground)'
  			},
  			popover: {
  				DEFAULT: 'var(--color-popover)',
  				foreground: 'var(--color-popover-foreground)'
  			},
  			primary: {
  				DEFAULT: 'var(--color-primary)',
  				foreground: 'var(--color-primary-foreground)'
  			},
  			secondary: {
  				DEFAULT: 'var(--color-secondary)',
  				foreground: 'var(--color-secondary-foreground)'
  			},
  			muted: {
  				'10': 'rgb(var(--color-muted) / 0.1)',
  				'20': 'rgb(var(--color-muted) / 0.2)',
  				DEFAULT: 'rgb(var(--color-muted))',
  				foreground: 'rgb(var(--color-muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'var(--color-accent)',
  				foreground: 'var(--color-accent-foreground)'
  			},
  			primaryAccent: {
  				DEFAULT: 'var(--color-primary-accent)',
  				foreground: 'var(--color-primary-accent-foreground)'
  			},
  			destructive: {
  				DEFAULT: 'var(--color-destructive)',
  				foreground: 'var(--color-destructive-foreground)'
  			},
  			border: 'var(--color-border)',
  			input: 'var(--color-input)',
  			ring: 'var(--color-ring)',
  			chart: {
  				'1': 'var(--color-chart-1)',
  				'2': 'var(--color-chart-2)',
  				'3': 'var(--color-chart-3)',
  				'4': 'var(--color-chart-4)',
  				'5': 'var(--color-chart-5)'
  			},
  			sidebar: {
  				DEFAULT: 'hsl(var(--sidebar-background))',
  				foreground: 'hsl(var(--sidebar-foreground))',
  				primary: 'hsl(var(--sidebar-primary))',
  				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
  				accent: 'hsl(var(--sidebar-accent))',
  				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
  				border: 'hsl(var(--sidebar-border))',
  				ring: 'hsl(var(--sidebar-ring))'
  			}
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
  safelist: [
    'bg-backgroundSecondary',
    'text-foreground',
    'border-muted',
  ],
};
