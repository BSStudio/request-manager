import { useLayoutEffect, useRef } from 'react';

import { cn } from 'cn';
import {
  Outlet,
  ScrollRestoration,
  useLocation,
  useMatches,
} from 'react-router';

import AppStatus from 'site/components/AppStatus';
import SiteFooter from 'site/components/SiteFooter';
import SiteHeader from 'site/components/SiteHeader';

export type SiteRouteHandle = {
  // The page starts with a dark hero that the header can sit on.
  overlayHeader?: boolean;
};

// Anchors on the same page glide, changing pages jumps
function ScrollBehavior() {
  const { hash, pathname } = useLocation();
  const previousPath = useRef<string | null>(null);

  useLayoutEffect(() => {
    const samePage = previousPath.current === pathname;
    previousPath.current = pathname;
    document.documentElement.toggleAttribute(
      'data-smooth-scroll',
      samePage && hash !== '',
    );
  }, [hash, pathname]);

  return null;
}

export default function Layout() {
  const matches = useMatches();
  const overlayHeader = matches.some(
    (match) => (match.handle as SiteRouteHandle | undefined)?.overlayHeader,
  );

  return (
    <div className="flex min-h-svh flex-col">
      <SiteHeader overlay={overlayHeader} />
      <main
        className={cn(
          'flex flex-1 flex-col',
          !overlayHeader && 'pt-[calc(4rem+env(safe-area-inset-top))]',
        )}
      >
        <Outlet />
      </main>
      <SiteFooter />
      <AppStatus />
      <ScrollBehavior />
      <ScrollRestoration />
    </div>
  );
}
