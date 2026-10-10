/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vanilla: {
          DEFAULT: '#FFFAED',
          light: '#FFFDF8',
          deep: '#F5EEDB',
          darker: '#EAE1CE',
        },
        iris: {
          DEFAULT: '#95A1D8',
          light: '#C2CAEC',
          soft: '#E8ECFA',
          deep: '#7382C4',
        },
        atlantic: {
          DEFAULT: '#275992',
          deep: '#132E4F',
          dark: '#0E2139',
          hover: '#1E4775',
          soft: '#EBF2FA',
        },
        navy: {
          DEFAULT: '#132E4F',
          muted: '#4A5D75',
          light: '#657B94',
        },
        coral: {
          DEFAULT: '#E06D53',
          soft: '#FDEEEA',
        },
        amber: {
          DEFAULT: '#DFA038',
          soft: '#FEF7E8',
        },
        sage: {
          DEFAULT: '#528A74',
          soft: '#EEF6F3',
        },
        // Backwards compatibility with app routes
        appBg: '#FFFAED',
        cardBg: '#FFFDF8',
        cardBorder: '#EFE5D2',
        textMain: '#132E4F',
        textMuted: '#586D85',
        danger: '#E06D53',
        success: '#528A74',
      },
      fontFamily: {
        heading: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
        body: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        '2xl': '1.25rem',
        '3xl': '1.75rem',
        '4xl': '2.25rem',
      },
      boxShadow: {
        'iris-soft': '0 20px 45px -15px rgba(149, 161, 216, 0.25)',
        'iris-glow': '0 0 35px 5px rgba(149, 161, 216, 0.35)',
        'atlantic-glow': '0 8px 25px -4px rgba(39, 89, 146, 0.35)',
        'cream-card': '0 15px 35px -10px rgba(149, 161, 216, 0.18), 0 0 0 1px rgba(255, 255, 255, 0.8) inset',
        'glass-hover': '0 25px 50px -12px rgba(149, 161, 216, 0.28), 0 0 0 1px rgba(255, 255, 255, 0.95) inset',
      }
    },
  },
  plugins: [],
}
