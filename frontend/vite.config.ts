import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Finance App',
        short_name: 'Finance',
        description: 'Controle financeiro pessoal — orçamento, transações e saúde financeira',
        theme_color: '#0f766e',
        background_color: '#0b1220',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any maskable' },
        ],
      },
      workbox: {
        // navegação offline cai na shell do app; dados (API) nunca ficam em
        // cache automático aqui — isso é responsabilidade de uma entrega futura
        navigateFallback: '/index.html',
      },
    }),
  ],
})
