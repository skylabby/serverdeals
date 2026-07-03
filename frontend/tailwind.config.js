/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Fira Sans"', 'system-ui', 'sans-serif'],
        mono: ['"Fira Code"', 'monospace'],
      },
      colors: {
        // "Financial Dashboard" palette — dark navy + green accents for deal savings
        brand: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          950: '#052e16',
        },
        surface: {
          DEFAULT: '#020617',  // bg
          raised: '#0e1223',   // card
          overlay: '#1b2336',  // hover / elevated
        },
        border: {
          DEFAULT: '#334155',
          subtle: '#1e293b',
        },
        // Deal classification colors
        deal: {
          hot: '#22c55e',    // brand-500 — =40% below median
          good: '#eab308',   // yellow — 20-39%
          fair: '#94a3b8',   // slate-400 — 0-19%
        },
      },
    },
  },
  plugins: [],
};
