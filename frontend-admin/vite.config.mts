import path from 'path';

import tailwindcss from '@tailwindcss/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
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
    port: 5173,
  },
});
