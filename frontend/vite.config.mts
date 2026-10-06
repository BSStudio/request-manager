import path from 'path';

import tailwindcss from '@tailwindcss/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const { BACKEND_URL } = loadEnv(mode, import.meta.dirname, '');

  return {
    build: {
      assetsDir: 'static/frontend',
      outDir: 'build',
      // sourcemap: true, // When you want to use source-map-explorer
    },
    plugins: [
      basicSsl(),
      react(),
      tailwindcss(),
      VitePWA({
        filename: 'sw.ts',
        injectManifest: {
          globIgnores: ['service-worker.js'],
          // Fonts and images are cached by the worker when first used.
          globPatterns: ['index.html', '**/*.{css,js}', '*.{png,svg}'],
        },
        injectRegister: false,
        manifest: {
          background_color: '#070d18',
          description:
            'A Budavári Schönherz Stúdió forgatási és élő közvetítési felkéréseit kezelő rendszere.',
          display: 'standalone',
          icons: [
            { sizes: '64x64', src: 'pwa-64x64.png', type: 'image/png' },
            { sizes: '192x192', src: 'pwa-192x192.png', type: 'image/png' },
            { sizes: '512x512', src: 'pwa-512x512.png', type: 'image/png' },
            {
              purpose: 'maskable',
              sizes: '512x512',
              src: 'maskable-icon-512x512.png',
              type: 'image/png',
            },
          ],
          id: '/',
          lang: 'hu',
          name: 'BSS Felkéréskezelő',
          scope: '/',
          short_name: 'Felkéréskezelő',
          shortcuts: [
            {
              icons: [{ sizes: '192x192', src: 'pwa-192x192.png' }],
              name: 'Felkérés beküldése',
              url: '/new-request',
            },
            {
              icons: [{ sizes: '192x192', src: 'pwa-192x192.png' }],
              name: 'Felkéréseim',
              url: '/my-requests',
            },
            {
              icons: [{ sizes: '192x192', src: 'pwa-192x192.png' }],
              name: 'Admin felület',
              url: '/admin',
            },
          ],
          start_url: '/',
          theme_color: '#070d18',
        },
        registerType: 'prompt',
        srcDir: 'src',
        strategies: 'injectManifest',
      }),
    ],
    resolve: {
      alias: {
        '~primereact': path.resolve(
          import.meta.dirname,
          'node_modules/primereact',
        ),
      },
      tsconfigPaths: true,
    },
    server: {
      proxy: {
        // Same origin for the session cookie, as Django serves the app in
        // production. The header lets Django see the page's HTTPS origin.
        '/api': {
          headers: { 'X-Forwarded-Proto': 'https' },
          target: BACKEND_URL || 'http://localhost:8000',
        },
      },
    },
  };
});
