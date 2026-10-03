import { cn } from 'cn';
import { ArrowRightIcon } from 'lucide-react';
import { Link, useLocation } from 'react-router';

import BssLogo from 'site/components/BssLogo';
import MobileNav from 'site/components/MobileNav';
import ThemeToggle from 'site/components/ThemeToggle';
import { Button } from 'site/components/ui/button';
import UserMenu from 'site/components/UserMenu';
import { useScrolled } from 'site/hooks/useScrolled';
import { useSessionUser } from 'site/lib/session';

// Over a dark hero the header is see-through until the page is scrolled. The
// buttons follow the header's colour fade, a transition of their own would lag.
const onDark =
  'transition-[background-color,border-color,box-shadow,transform] group-data-transparent/header:text-white group-data-transparent/header:hover:bg-white/10 group-data-transparent/header:hover:text-white group-data-transparent/header:aria-expanded:bg-white/10 group-data-transparent/header:aria-expanded:text-white';

export default function SiteHeader({ overlay }: { overlay: boolean }) {
  const user = useSessionUser();
  const scrolled = useScrolled();
  const location = useLocation();
  const transparent = overlay && !scrolled;

  return (
    <header
      className={cn(
        'group/header fixed inset-x-0 top-0 z-50 border-b pt-[env(safe-area-inset-top)] transition-[background-color,border-color,color] duration-300',
        transparent
          ? 'border-transparent text-white'
          : 'border-border/70 bg-background/80 backdrop-blur-xl',
      )}
      data-transparent={transparent || undefined}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4 sm:px-6">
        <Link
          aria-label="Kezdőlap"
          className="flex items-center gap-3 rounded-md outline-offset-4"
          to="/"
        >
          <BssLogo className="h-7 w-auto" mono={transparent} />
          <span className="border-l border-current/20 pl-3 font-heading text-[1.0625rem] font-semibold tracking-tight">
            Felkéréskezelő
          </span>
        </Link>
        <div className="ml-auto hidden items-center gap-1 md:flex">
          <ThemeToggle className={onDark} />
          {user && <UserMenu className={onDark} user={user} />}
          {!user && location.pathname !== '/login' && (
            <Button asChild className={onDark} variant="ghost">
              <Link state={{ from: location.pathname }} to="/login">
                Bejelentkezés
              </Link>
            </Button>
          )}
          {location.pathname !== '/new-request' && (
            <Button
              asChild
              className="ml-2 duration-300 group-data-transparent/header:bg-white group-data-transparent/header:text-ink group-data-transparent/header:hover:bg-white/85"
            >
              <Link to="/new-request">
                Felkérés beküldése
                <ArrowRightIcon data-icon="inline-end" />
              </Link>
            </Button>
          )}
        </div>
        <MobileNav
          className={cn('-mr-2 ml-auto md:hidden', onDark)}
          user={user}
        />
      </div>
    </header>
  );
}
