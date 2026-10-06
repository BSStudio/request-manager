import type { CSSProperties } from 'react';

import type { AvatarProviderEnum } from 'api/models';

export const avatarProviderLabels: Record<AvatarProviderEnum, string> = {
  'google-oauth2': 'Google',
  gravatar: 'Gravatar',
  'microsoft-graph': 'Microsoft',
};

const avatarColors = [
  '#2563eb',
  '#4f46e5',
  '#7c3aed',
  '#a21caf',
  '#be185d',
  '#b91c1c',
  '#c2410c',
  '#b45309',
  '#3f6212',
  '#15803d',
  '#0f766e',
  '#0369a1',
];

// A name always gets the same color, so people with the same initials can
// still be told apart.
function getAvatarColor(name: string) {
  // FNV-1a, then MurmurHash3's finalizer to spread it over the low bits.
  let hash = 0x811c9dc5;
  for (const char of name.trim().toLowerCase().replace(/\s+/g, ' ')) {
    hash = Math.imul(hash ^ (char.codePointAt(0) ?? 0), 0x01000193);
  }
  hash = Math.imul(hash ^ (hash >>> 16), 0x85ebca6b);
  hash = Math.imul(hash ^ (hash >>> 13), 0xc2b2ae35);
  hash ^= hash >>> 16;
  return avatarColors[(hash >>> 0) % avatarColors.length];
}

// A light tint with text in the same hue, at least 5.9:1 on both themes. The
// admin reloads when its theme changes, so reading the class once is enough.
export function getAvatarStyle(name: string): CSSProperties {
  const color = getAvatarColor(name);
  const dark = document.documentElement.classList.contains('dark');
  return {
    backgroundColor: `color-mix(in oklab, ${color} 18%, transparent)`,
    color: dark
      ? `color-mix(in oklab, ${color} 45%, white)`
      : `color-mix(in oklab, ${color} 80%, black)`,
  };
}

export function getInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => [...part][0])
    .join('')
    .toUpperCase();
}
