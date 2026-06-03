// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['shadcn-nuxt', '@nuxtjs/tailwindcss', '@clerk/nuxt'],
  css: ['~/assets/css/tailwind.css'],
  
  tailwindcss: {
    exposeConfig: true,
    viewer: true,
  },

  routeRules: {
    '/dashboard/**': { appLayout: 'dashboard' },
  },

  shadcn: {
    prefix: '',
    componentDir: '@/components/ui'
  }
})