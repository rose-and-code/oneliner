/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{wxml,ts,js}'],
  theme: {
    extend: {
      colors: {
        bg: '#0A0F0E',
        'bg-card': 'rgba(255, 255, 255, 0.035)',
        'bg-back': 'rgba(255, 255, 255, 0.025)',
        text: '#E8F0EC',
        'text-secondary': '#9AADA2',
        'text-dim': '#546E64',
        'text-faint': '#2E4A40',
        accent: '#34D399',
        'accent-warm': '#F0A050',
        'accent-muted': 'rgba(52, 211, 153, 0.14)',
        'accent-dim': 'rgba(52, 211, 153, 0.07)',
        divider: 'rgba(52, 211, 153, 0.08)',
      },
      borderRadius: {
        card: '20px',
        'card-lg': '28px',
      },
      fontFamily: {
        sans: ['"Noto Sans SC"', '-apple-system', '"SF Pro Rounded"', '"PingFang SC"', 'sans-serif'],
      },
      spacing: {
        safe: 'env(safe-area-inset-bottom, 0px)',
      },
    },
  },
  plugins: [],
}
