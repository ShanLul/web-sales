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
        success: '#2BA471',
        warning: '#E37318',
        danger: '#D54941',
      },
      fontFamily: {
        sans: ['"PingFang SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 2px 12px -6px rgba(0, 21, 41, 0.16)',
        bar: '0 -6px 24px -12px rgba(0, 21, 41, 0.28)',
      },
      keyframes: {
        pop: {
          '0%': { transform: 'scale(1)' },
          '45%': { transform: 'scale(1.12)' },
          '100%': { transform: 'scale(1)' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'check-pop': {
          '0%': { transform: 'scale(0.5)', opacity: '0' },
          '60%': { transform: 'scale(1.08)', opacity: '1' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      animation: {
        pop: 'pop 0.32s ease-out',
        'fade-up': 'fade-up 0.3s ease-out both',
        'check-pop': 'check-pop 0.45s ease-out both',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
