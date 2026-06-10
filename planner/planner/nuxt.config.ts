// nuxt.config.ts
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  
  // Habilitar SPA para evitar problemas de IndexedDB en el lado del servidor (SSR)
  ssr: false,

  devtools: { enabled: true },

  // Cargar CSS global
  css: [
    '~/assets/css/main.css'
  ],

  future: {
    compatibilityVersion: 4
  },

  app: {
    head: {
      title: 'FS25 Farm Planner',
      meta: [
        { name: 'description', content: 'Herramienta de planificación y toma de decisiones para Farming Simulator 25' }
      ]
    }
  }
})
