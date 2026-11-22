/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        carbon: {
          bg: '#0C0D0E',
          surface: '#121417',
          elevated: '#181B1F',
          deep: '#090A0B',
          primary: '#121417',
          secondary: '#181B1F',
        },
        silver: {
          light: '#F0F2F5',
          primary: '#F0F2F5',
          secondary: '#8E95A0',
          muted: '#636B78',
          border: '#20242A',
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
      },
    },
  },
  plugins: [],
};
