/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      colors: {
        brand: {
          dark: '#1a1a2e',
          dark2: '#16213e',
        },
        perf: {
          green: '#4CAF50',
          yellow: '#FFC107',
          red: '#F44336',
        },
      },
    },
  },
  plugins: [],
}
