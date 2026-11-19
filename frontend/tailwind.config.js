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
          deep: '#111315',
          primary: '#111315',
          secondary: '#191C1F',
          surface: '#22262A',
        },
        silver: {
          light: '#F0F1F2',
          primary: '#F0F1F2',
          secondary: '#A0A6AC',
          border: '#343A3F',
        },
        signal: {
          yellow: '#E5B83D',
          hover: '#F2C64B',
          muted: '#B58D2D',
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

