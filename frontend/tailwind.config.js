/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Legacy tokens — still used by existing pages
        brand: {
          dark: '#1a1a2e',
          dark2: '#16213e',
          // Dashboard redesign brand dot colors
          salta: 'oklch(0.72 0.16 240)',
          heine: 'oklch(0.78 0.16 145)',
          imper: 'oklch(0.80 0.17 75)',
          mille: 'oklch(0.82 0.15 90)',
          multi: 'oklch(0.72 0.16 300)',
          impor: 'oklch(0.70 0.18 27)',
        },
        perf: {
          green: '#4CAF50',
          yellow: '#FFC107',
          red: '#F44336',
        },
        // Dashboard redesign tokens
        bg: {
          0: '#0e0d0b',
          1: '#17150f',
          2: '#1e1b14',
          3: '#26221a',
        },
        line: {
          DEFAULT: '#2e2a20',
          2: '#3a3527',
        },
        ink: {
          0: '#f5efdd',
          1: '#d9d2bd',
          2: '#928a75',
          3: '#6a6353',
        },
        danger: 'oklch(0.70 0.18 27)',
        warn:   'oklch(0.78 0.16 70)',
        ok:     'oklch(0.78 0.16 145)',
        info:   'oklch(0.78 0.14 230)',
        violet: 'oklch(0.72 0.16 300)',
        lime:   'oklch(0.86 0.18 115)',
      },
      borderRadius: {
        xl2: '11px',
        xl3: '22px',
      },
      boxShadow: {
        rail: '0 8px 24px rgba(0,0,0,0.35)',
        'lime-glow': '0 0 8px oklch(0.86 0.18 115)',
      },
      backdropBlur: {
        rail: '12px',
      },
    },
  },
  plugins: [],
}
