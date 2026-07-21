/** Tema oscuro "paño de casino": verde profundo, crema de naipe y ámbar. */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        felt:  { 950: '#0A100D', 900: '#0E1713', 800: '#14211B', 700: '#1C2E25', 600: '#274033' },
        naipe: '#F2EDE0',
        ambar: { DEFAULT: '#D4A94A', dim: '#8A6F33' },
        gana:  '#3FA96B',
        pierde:'#C4453B'
      },
      fontFamily: {
        num: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace']
      },
      boxShadow: {
        card: '0 2px 6px rgba(0,0,0,.45)',
        panel: '0 -8px 32px rgba(0,0,0,.6)'
      }
    }
  },
  plugins: []
}
