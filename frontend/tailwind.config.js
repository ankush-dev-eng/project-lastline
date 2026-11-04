/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#14181B',
          muted: '#20262B',
          border: '#2A3238',
        },
        basalt: {
          DEFAULT: '#1D2327',
          surface: '#242C31',
          subtle: '#2E383F',
        },
        bone: {
          DEFAULT: '#F2EFE8',
          subtle: '#E8E4DA',
          muted: '#DFD9CD',
        },
        stone: {
          DEFAULT: '#D9D4C7',
          border: '#C5BFAe',
        },
        sage: {
          DEFAULT: '#6F8F7B',
          hover: '#5F7F6B',
          subtle: 'rgba(111, 143, 123, 0.15)',
        },
        moss: {
          DEFAULT: '#4F7A5A',
          subtle: 'rgba(79, 122, 90, 0.15)',
        },
        brass: {
          DEFAULT: '#C79A3B',
          subtle: 'rgba(199, 154, 59, 0.15)',
        },
        copper: {
          DEFAULT: '#B5693E',
          subtle: 'rgba(181, 105, 62, 0.15)',
        },
        brick: {
          DEFAULT: '#A8403A',
          subtle: 'rgba(168, 64, 58, 0.15)',
        },
      },
      fontFamily: {
        sans: ['"Instrument Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      fontFeatureSettings: {
        numeric: '"tnum" on, "lnum" on',
      },
    },
  },
  plugins: [],
}
