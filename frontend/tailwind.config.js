/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      // Civic-blue palette per docs/design/design-spec.md — all pairings WCAG AA verified
      colors: {
        primary: {
          50: '#f0f6fb',
          100: '#dbeaf5',
          200: '#b7d5ec',
          300: '#85b7dd',
          400: '#4f94c9',
          500: '#2b7fbe',
          600: '#1d70b8',
          700: '#175a94',
          800: '#124873',
          900: '#0d3453',
        },
        success: {
          50: '#f0fdf4',
          600: '#0f7a52',
          800: '#166534',
        },
      },
      fontFamily: {
        sans: ['"Public Sans"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"',
               'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
      },
      fontSize: {
        base: ['1.0625rem', { lineHeight: '1.6' }],
      },
    },
  },
  plugins: [],
}
