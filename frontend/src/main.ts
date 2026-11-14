import { createApp } from 'vue'
import App from './App.vue'
import { consumeKeyFromLocation } from './api/access'
import { router } from './router'
import './styles.css'

// До старта роутера: прочитать #key= из ссылки на дело и сразу убрать его из адреса.
consumeKeyFromLocation()
// Если ключ вставили в уже открытой вкладке (меняется только фрагмент) — перезагрузим экран с новым ключом.
window.addEventListener('hashchange', () => { if (consumeKeyFromLocation()) window.location.reload() })

createApp(App).use(router).mount('#app')
