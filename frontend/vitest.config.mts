import { defineConfig } from 'vitest/config';

// Separate from vite.config.mts, so tests skip its SSL, PWA and Sentry plugins.
export default defineConfig({
  resolve: {
    tsconfigPaths: true,
  },
  test: {
    coverage: {
      exclude: [
        // The generated API client.
        'src/api/{api,base,common,configuration,index}.ts',
        'src/api/{endpoints,models}/**',
      ],
      include: ['src/**/*.{ts,tsx}'],
    },
    environment: 'jsdom',
    // CI runs in UTC, the app formats dates for Hungary.
    env: { TZ: 'Europe/Budapest' },
  },
});
