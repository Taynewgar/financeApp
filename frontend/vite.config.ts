import { execSync } from 'node:child_process'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Identifica exatamente qual commit está rodando (item do backlog: "qual
// versão está carregada no navegador/mobile"). A Vercel expõe o SHA do
// commit em build de produção — fora dela (dev/build local) cai pro git
// local; se nem isso existir (checkout sem histórico), fica "dev".
function commitVersao(): string {
  const shaVercel = process.env.VERCEL_GIT_COMMIT_SHA
  if (shaVercel) return shaVercel.slice(0, 7)
  try {
    return execSync('git rev-parse --short HEAD').toString().trim()
  } catch {
    return 'dev'
  }
}

// https://vite.dev/config/
export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(commitVersao()),
    __APP_BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
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
