import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [vue()],
    server: {
      // Dev-прокси: фронт ходит на относительный /api, секреты не попадают в URL.
      proxy: { '/api': env.VITE_API_PROXY || 'http://localhost:8000' },
    },
    build: { target: 'es2020' },
  }
})
