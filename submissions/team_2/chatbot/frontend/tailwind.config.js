/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'graphmind-blue': '#3B82F6',
        'graphmind-dark': '#0a0a0a',
        'graphmind-card': '#1a1a2e',
      },
    },
  },
  plugins: [],
}
