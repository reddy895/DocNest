/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#212121',
        sidebar: '#171717',
        composer: '#303030',
        hover: '#2F2F2F',
        surface: {
          DEFAULT: '#2A2A2A',
          raised: '#171717',
          sunken: '#212121',
          hover: '#2F2F2F',
        },
        border: {
          DEFAULT: '#3A3A3A',
          subtle: '#2E2E2E',
        },
        foreground: '#ECECEC',
        muted: {
          DEFAULT: '#A1A1A1',
          dim: '#777777',
        },
        brand: {
          DEFAULT: '#F0F0F0',
          hover: '#FFFFFF',
          foreground: '#171717',
          muted: '#A1A1A1',
        },
        carbon: {
          bg: '#212121',
          surface: '#171717',
          elevated: '#2A2A2A',
          deep: '#171717',
          primary: '#171717',
          secondary: '#2A2A2A',
        },
        silver: {
          light: '#ECECEC',
          primary: '#ECECEC',
          secondary: '#A1A1A1',
          muted: '#777777',
          border: '#3A3A3A',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'carbon-sm': '0 1px 2px rgba(0, 0, 0, 0.25)',
        'carbon-md': '0 4px 12px rgba(0, 0, 0, 0.3)',
        'carbon-lg': '0 8px 24px rgba(0, 0, 0, 0.4)',
        'focus-brand': '0 0 0 1px rgba(236, 236, 236, 0.3)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.45' },
        },
      },
      animation: {
        'fade-in': 'fade-in 160ms ease-out both',
        'slide-up': 'slide-up 200ms ease-out both',
        'pulse-soft': 'pulse-soft 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
