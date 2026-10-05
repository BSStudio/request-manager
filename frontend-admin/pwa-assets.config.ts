import {
  defineConfig,
  minimal2023Preset,
} from '@vite-pwa/assets-generator/config';

// The icon already fills the whole square, so nothing is padded. The existing
// favicon.ico is kept.
export default defineConfig({
  images: ['public/icon.svg'],
  preset: {
    ...minimal2023Preset,
    apple: { ...minimal2023Preset.apple, padding: 0 },
    maskable: { ...minimal2023Preset.maskable, padding: 0 },
    transparent: {
      ...minimal2023Preset.transparent,
      favicons: [],
      padding: 0,
    },
  },
});
