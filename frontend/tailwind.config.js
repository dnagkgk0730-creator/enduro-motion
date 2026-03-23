/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:       '#0d0f14',
        surface:  '#161a22',
        surface2: '#1e2330',
        border:   '#2a3142',
        accent:   '#f97316',
        accent2:  '#3b82f6',
      },
    },
  },
  plugins: [],
}
