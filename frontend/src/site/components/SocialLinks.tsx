import { cn } from 'cn';
import { GlobeIcon } from 'lucide-react';

import {
  FacebookIcon,
  InstagramIcon,
  TikTokIcon,
  YouTubeIcon,
} from 'site/components/BrandIcons';

const links = [
  { href: 'https://bsstudio.hu', icon: GlobeIcon, label: 'Weboldal' },
  {
    href: 'https://facebook.com/bsstudio',
    icon: FacebookIcon,
    label: 'Facebook',
  },
  {
    href: 'https://instagram.com/budavari_schonherz_studio',
    icon: InstagramIcon,
    label: 'Instagram',
  },
  { href: 'https://tiktok.com/@bsstudio_', icon: TikTokIcon, label: 'TikTok' },
  { href: 'https://youtube.com/bsstudi0', icon: YouTubeIcon, label: 'YouTube' },
];

export default function SocialLinks({ className }: { className?: string }) {
  return (
    <ul className={cn('flex flex-wrap items-center gap-2', className)}>
      {links.map(({ href, icon: Icon, label }) => (
        <li key={href}>
          <a
            aria-label={label}
            className="grid size-10 place-items-center rounded-full border border-current/15 opacity-70 transition hover:border-current/40 hover:bg-current/10 hover:opacity-100 focus-visible:opacity-100"
            href={href}
            rel="noreferrer"
            target="_blank"
            title={label}
          >
            <Icon className="size-4.5" />
          </a>
        </li>
      ))}
    </ul>
  );
}
