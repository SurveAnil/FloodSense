/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#172033',
        muted: '#667085',
        surface: '#ffffff',
        canvas: '#f6f8fb',
        line: '#e4e8ef',
        low: '#238b62',
        moderate: '#b7791f',
        high: '#d95d17',
        critical: '#c43d4b',
      },
      boxShadow: {
        panel: '0 4px 18px rgba(23, 32, 51, 0.06)',
      },
    },
  },
  plugins: [],
};
