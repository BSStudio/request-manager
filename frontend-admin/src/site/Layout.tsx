import { cn } from 'cn';
import { Outlet, ScrollRestoration, useMatches } from 'react-router';

import SiteFooter from 'site/components/SiteFooter';
import SiteHeader from 'site/components/SiteHeader';

export type SiteRouteHandle = {
  // The page starts with a dark hero that the header can sit on.
  overlayHeader?: boolean;
};

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
      <ScrollRestoration />
    </div>
  );
}
