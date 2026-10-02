import path from 'path';

import tailwindcss from '@tailwindcss/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    assetsDir: 'static/frontend-admin',
    outDir: 'build',
    // sourcemap: true, // When you want to use source-map-explorer
  },
  plugins: [basicSsl(), react(), tailwindcss(), tsconfigPaths()],
  resolve: {
    alias: {
      '~primereact': path.resolve(__dirname, 'node_modules/primereact'),
    },
  },
  server: {
    port: 5173,
  },
});
