/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'slate': {
          50: '#f8fafc',
          950: '#0f172a',
        },
        // Silent-luxury palette: off-white, warm gold, deep black.
        'bone': {
          50: '#faf8f5',
          100: '#f2ede5',
          200: '#e3dbcd',
          300: '#cabfab',
        },
        'gold': {
          200: '#e8d5a8',
          300: '#d8bd82',
          400: '#c9a961',
          500: '#b8944a',
          600: '#96763a',
        },
        'ink': {
          800: '#161514',
          900: '#0e0d0c',
          950: '#070706',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
      },
      letterSpacing: {
        luxe: '0.22em',
      },
    },
  },
  plugins: [],
}
