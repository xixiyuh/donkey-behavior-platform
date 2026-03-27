import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router/index.ts'
import App from './App.vue'
import './style.css'

console.log('main.ts loaded')
console.log('router:', router)

const app = createApp(App)

console.log('app created')

app.use(createPinia())
app.use(router)

console.log('router added to app')

app.mount('#app')

console.log('app mounted')
