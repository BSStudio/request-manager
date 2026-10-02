import { ArrowUpRightIcon } from 'lucide-react';
import { Link } from 'react-router';

import BssLogo from 'site/components/BssLogo';
import SocialLinks from 'site/components/SocialLinks';
import { useSessionUser } from 'site/lib/session';

type FooterLink = { external?: boolean; label: string; to: string };

function FooterColumn({
  links,
  title,
}: {
  links: FooterLink[];
  title: string;
}) {
  return (
    <nav aria-label={title}>
      <h2 className="font-mono text-xs tracking-[0.18em] text-white/45 uppercase">
        {title}
      </h2>
      <ul className="mt-4 space-y-3 text-sm">
        {links.map(({ external, label, to }) => (
          <li key={label}>
            {external ? (
              <a
                className="group inline-flex items-center gap-1 text-white/75 transition-colors hover:text-white"
                href={to}
                rel="noreferrer"
                target={to.startsWith('http') ? '_blank' : undefined}
              >
                {label}
                <ArrowUpRightIcon className="size-3.5 opacity-50 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100" />
              </a>
            ) : (
              <Link
                className="text-white/75 transition-colors hover:text-white"
                to={to}
              >
                {label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default function SiteFooter() {
  const user = useSessionUser();

  return (
    <footer className="bg-ink pb-[env(safe-area-inset-bottom)] text-ink-foreground">
      <div className="mx-auto max-w-6xl px-4 pt-16 pb-10 sm:px-6">
        <div className="grid grid-cols-2 gap-x-6 gap-y-10 lg:grid-cols-[1.6fr_1fr_1fr_1fr]">
          <div className="col-span-2 max-w-xs lg:col-span-1">
            <Link
              aria-label="Kezdőlap"
              className="inline-flex items-center gap-3"
              to="/"
            >
              <BssLogo className="h-8 w-auto text-white" mono />
              <span className="border-l border-white/20 pl-3 font-heading text-lg font-semibold">
                Felkéréskezelő
              </span>
            </Link>
            <p className="mt-5 text-sm leading-relaxed text-white/60">
              A Budavári Schönherz Stúdió forgatási és élő közvetítési
              felkéréseit kezelő rendszere.
            </p>
          </div>
          <FooterColumn
            links={[
              { label: 'Felkérés beküldése', to: '/new-request' },
              ...(user
                ? [
                    { label: 'Felkéréseim', to: '/my-requests' },
                    { label: 'Profilom', to: '/profile' },
                  ]
                : [{ label: 'Bejelentkezés', to: '/login' }]),
            ]}
            title="Felkérőknek"
          />
          <FooterColumn
            links={[
              {
                external: true,
                label: 'bsstudio.hu',
                to: 'https://bsstudio.hu',
              },
              {
                external: true,
                label: 'Korábbi videóink',
                to: 'https://bsstudio.hu/video/latest',
              },
              {
                external: true,
                label: 'info@bsstudio.hu',
                to: 'mailto:info@bsstudio.hu',
              },
            ]}
            title="Stúdió"
          />
          <FooterColumn
            links={[
              { label: 'Adatvédelmi irányelvek', to: '/privacy' },
              { label: 'Szolgáltatási feltételek', to: '/terms' },
            ]}
            title="Jogi tudnivalók"
          />
        </div>
        <div className="mt-14 flex flex-col gap-8 border-t border-white/10 pt-8 md:flex-row md:items-center md:justify-between">
          <SocialLinks className="text-white md:order-last" />
          <p className="text-sm text-white/50">
            © {new Date().getFullYear()} Budavári Schönherz Stúdió
          </p>
        </div>
      </div>
    </footer>
  );
}
