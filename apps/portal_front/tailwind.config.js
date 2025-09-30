/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#0f172a',
          accent: '#2563eb',
          success: '#16a34a',
          warning: '#f59e0b',
        },
      },
      spacing: {
        '1.5': '0.375rem',
        '2.5': '0.625rem',
        '3.5': '0.875rem',
      },
      fontSize: {
        '2xs': '0.75rem',
        'xs': '0.8125rem',
      },
      boxShadow: {
        'card': '0 6px 24px rgba(15, 23, 42, 0.08)',
      },
      borderRadius: {
        'xl': '0.875rem',
        '2xl': '1rem',
      },
    },
  },
  plugins: [],
};
