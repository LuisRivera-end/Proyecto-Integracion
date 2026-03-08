// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: false },

  app: {
    head: {
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      htmlAttrs: { lang: 'es' },
    },
  },

  css: [
    '~/assets/css/main.css',
    'toastify-js/src/toastify.css',
  ],

  vite: {
    plugins: [
      // @ts-ignore
      import('@tailwindcss/vite').then(m => m.default()),
    ],
  },

  // SSR enabled by default — good for initial load, but since this app
  // is mostly client-side interactive, pages use client-only components
  ssr: false,
})
