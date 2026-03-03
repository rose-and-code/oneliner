/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{wxml,ts,js}'],
  theme: {
    extend: {
      colors: {
        bg: '#F2EDE7',
        'bg-card': '#FFFFFF',
        text: '#1A1A1A',
        'text-secondary': 'rgba(26, 26, 26, 0.45)',
        'text-dim': 'rgba(26, 26, 26, 0.3)',
        'text-faint': 'rgba(26, 26, 26, 0.18)',
        accent: '#1A1A1A',
        divider: 'rgba(26, 26, 26, 0.06)',
      },
      borderRadius: {
        card: '20px',
        'card-lg': '28px',
        pill: '50px',
      },
      fontFamily: {
        sans: ['-apple-system', '"SF Pro Rounded"', '"PingFang SC"', '"Noto Sans SC"', 'sans-serif'],
      },
      spacing: {
        safe: 'env(safe-area-inset-bottom, 0px)',
      },
    },
  },
  plugins: [],
}
