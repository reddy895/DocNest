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
          deep: '#171A1C',
          primary: '#202326',
          secondary: '#292D30',
          surface: '#303538',
        },
        silver: {
          light: '#E0E3E5',
          primary: '#BFC3C7',
          secondary: '#969DA3',
          border: '#555C61',
        },
        signal: {
          yellow: '#F4D21F',
          hover: '#FFDF45',
          muted: '#B99E16',
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

