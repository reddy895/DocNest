/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#101214',
        surface: {
          DEFAULT: '#1A1D20',
          raised: '#17191B',
          sunken: '#101214',
        },
        border: {
          DEFAULT: '#30353A',
          subtle: '#262B30',
        },
        foreground: '#F2F3F4',
        muted: '#B8BEC4',
        brand: {
          DEFAULT: '#F5C542',
          hover: '#FFD358',
          foreground: '#17191B',
          muted: '#C49826',
        },
        carbon: {
          bg: '#101214',
          surface: '#17191B',
          elevated: '#1A1D20',
          deep: '#0B0D0F',
          primary: '#17191B',
          secondary: '#1A1D20',
        },
        silver: {
          light: '#F2F3F4',
          primary: '#F2F3F4',
          secondary: '#B8BEC4',
          muted: '#8E95A0',
          border: '#30353A',
        },
        yellow: {
          warm: '#F5C542',
          hover: '#FFD358',
          muted: '#C49826',
        },
        signal: {
          yellow: '#F5C542',
          hover: '#FFD358',
          muted: '#C49826',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'carbon-sm': '0 1px 2px rgba(0, 0, 0, 0.3)',
        'carbon-md': '0 4px 12px rgba(0, 0, 0, 0.4)',
        'carbon-lg': '0 8px 24px rgba(0, 0, 0, 0.5)',
        'focus-brand': '0 0 0 2px rgba(245, 197, 66, 0.35)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.55' },
        },
      },
      animation: {
        'fade-in': 'fade-in 180ms ease-out both',
        'slide-up': 'slide-up 220ms ease-out both',
        'pulse-soft': 'pulse-soft 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
