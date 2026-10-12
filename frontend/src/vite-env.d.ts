/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// injetado em vite.config.ts (define) — hash curto do commit em produção
// (via VERCEL_GIT_COMMIT_SHA) ou do git local em dev/build local.
declare const __APP_VERSION__: string
declare const __APP_BUILD_TIME__: string
