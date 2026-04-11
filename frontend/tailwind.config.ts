import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        background: 'hsl(var(--background))',
        'text-primary': '#111827',
        'text-secondary': '#6B7280',
        border: 'hsl(var(--border))',
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        pass: '#15803D',
        fail: '#B91C1C',
        card: 'hsl(var(--card))',
        primary: 'hsl(var(--primary))',
        muted: 'hsl(var(--muted))',
        ring: 'hsl(var(--ring))',
      },
      borderRadius: {
        DEFAULT: '0.375rem',
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
};

export default config;
