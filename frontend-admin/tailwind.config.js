/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#0052D9',
          light: '#366EF4',
          soft: '#E3F0FF',
          deep: '#002A6E',
        },
        ink: {
          DEFAULT: '#001529',
          muted: '#666666',
        },
        success: '#2BA471',
        warning: '#E37318',
        danger: '#D54941',
      },
      fontFamily: {
        sans: ['"PingFang SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(0, 21, 41, 0.04), 0 8px 24px -12px rgba(0, 21, 41, 0.16)',
        float: '0 12px 40px -16px rgba(0, 82, 217, 0.35)',
      },
      keyframes: {
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '20%, 60%': { transform: 'translateX(-6px)' },
          '40%, 80%': { transform: 'translateX(6px)' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        drift: {
          '0%, 100%': { transform: 'translate3d(0, 0, 0) scale(1)' },
          '50%': { transform: 'translate3d(0, -18px, 0) scale(1.06)' },
        },
      },
      animation: {
        shake: 'shake 0.4s ease-in-out',
        'fade-up': 'fade-up 0.35s ease-out both',
        drift: 'drift 9s ease-in-out infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
