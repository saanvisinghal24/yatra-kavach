import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig(({mode}) => ({
  plugins: [
    {name:'local-origin-default', transformIndexHtml:{order:'pre',handler:(html:string)=>html.replaceAll('%VITE_PUBLIC_ORIGIN%',loadEnv(mode, process.cwd()).VITE_PUBLIC_ORIGIN || 'http://localhost:5173')}},
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'Yatra Kavach · यात्रा कवच',
        short_name: 'Yatra Kavach',
        description: 'Offline-first pilgrim trail safety system for Himachal Pradesh',
        theme_color: '#2F4B3A',
        background_color: '#F3EFE6',
        display: 'standalone',
        id: '/', start_url: '/', scope: '/', lang: 'en-IN',
        orientation: 'portrait',
        icons: [
          {src: 'maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable'},
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        importScripts: ['/background-sync.js'],
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/api\/v1\/(yatras|weather|advisories)/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 86400
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      }
    })
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          leaflet: ['leaflet']
        }
      }
    }
  },
  preview: {port:5173,host:true,proxy:{'/api':'http://127.0.0.1:8000'}},
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
    port: 5173,
    host: true
  }
}));
