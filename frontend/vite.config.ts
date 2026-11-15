import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [vue()],
    base: env.VITE_BASE_PATH || '/',
    // Алиас @ нужен самому Vite (tsconfig paths его не настраивает).
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: {
      // Dev-прокси: фронт ходит на относительный /api; ключ только в заголовке Authorization.
      proxy: { '/api': env.VITE_API_PROXY || 'http://localhost:8000' },
    },
    build: { target: 'es2020' },
  }
})
