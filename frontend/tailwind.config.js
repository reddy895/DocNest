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
          bg: '#101214',
          surface: '#1A1D20',
          elevated: '#17191B',
          deep: '#101214',
          primary: '#17191B',
          secondary: '#1A1D20',
        },
        silver: {
          light: '#F2F3F4',
          primary: '#F2F3F4',
          secondary: '#A2A9B0',
          muted: '#B8BEC4',
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
        'carbon-sm': '0 1px 3px rgba(0, 0, 0, 0.4)',
        'carbon-md': '0 4px 14px rgba(0, 0, 0, 0.5)',
        'carbon-lg': '0 10px 30px rgba(0, 0, 0, 0.65)',
        'signal-glow': '0 0 15px rgba(244, 210, 31, 0.25)',
      },
    },
  },
  plugins: [],
};

