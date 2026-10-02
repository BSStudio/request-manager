import path from 'path';

import tailwindcss from '@tailwindcss/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const { BACKEND_URL } = loadEnv(mode, import.meta.dirname, '');

  return {
    build: {
      assetsDir: 'static/frontend-admin',
      outDir: 'build',
      // sourcemap: true, // When you want to use source-map-explorer
    },
    plugins: [basicSsl(), react(), tailwindcss()],
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
