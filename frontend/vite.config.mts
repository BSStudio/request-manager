import { execFileSync } from 'child_process';
import path from 'path';

import { sentryVitePlugin } from '@sentry/vite-plugin';
import tailwindcss from '@tailwindcss/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

function git(...args: string[]) {
  return execFileSync('git', args, {
    cwd: import.meta.dirname,
    stdio: ['ignore', 'pipe', 'ignore'],
  })
    .toString()
    .trim();
}

// Mirrors the "Resolve the version" step of
// .github/workflows/docker-publish.yml, which versions image builds.
function gitVersion() {
  try {
    const describe = git(
      'describe',
      '--tags',
      '--first-parent',
      '--long',
      '--abbrev=7',
      '--match=v[0-9]*.[0-9]*.[0-9]*',
      '--exclude=*-*',
    );
    const match = /^v(\d+\.\d+\.\d+)-(\d+)-g([0-9a-f]+)$/.exec(describe);
    if (!match) return '';
    const [, tag, distance, hash] = match;

    if (distance === '0' && git('status', '--porcelain') === '') return tag;

    // Later commits must sort higher in Sentry, which compares the revision
    // numerically and prereleases as text.
    const branch = git('branch', '--show-current').replace(
      /[^0-9A-Za-z-]/g,
      '-',
    );
    return branch === '' || branch === 'main'
      ? `${tag}.${distance}+${hash}`
      : `${tag}.${distance}+${branch}.${hash}`;
  } catch {
    // No git or no release tag, as in the Docker build and shallow clones.
    return '';
  }
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const { BACKEND_URL, VERSION } = loadEnv(mode, import.meta.dirname, '');
  const version = VERSION || gitVersion();
  // Release names are shared across the Sentry organization, hence the app
  // name. The backend reports the same release.
  const release = version && `request-manager@${version}`;

  return {
    build: {
      assetsDir: 'static/frontend',
      outDir: 'build',
      sourcemap: 'hidden',
    },
    define: {
      'import.meta.env.VERSION': JSON.stringify(version),
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
          // The service worker does not report to Sentry.
          sourcemap: false,
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
      // Injects the release, which the SDK reports as its release option, and,
      // given SENTRY_AUTH_TOKEN, uploads the source maps under it.
      sentryVitePlugin({
        // Docker caches a passed build step, so a failed upload would never
        // be retried.
        errorHandler: (error) => {
          throw error;
        },
        org: 'budavari-schonherz-studio',
        project: 'request-manager-frontend',
        // Only tagged versions become releases, created with their commits by
        // the release workflow. An empty name injects none, where the plugin
        // would otherwise fall back to the commit hash.
        release: {
          create: false,
          finalize: false,
          name: release,
          setCommits: false,
        },
        telemetry: false,
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
