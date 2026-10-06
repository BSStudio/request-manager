import { HouseIcon, RotateCwIcon } from 'lucide-react';
import { isRouteErrorResponse, Link, useRouteError } from 'react-router';

import { useReportRouteError } from 'hooks/useReportRouteError';
import NoSignal from 'site/components/NoSignal';
import { Button } from 'site/components/ui/button';
import { usePageTitle } from 'site/hooks/usePageTitle';
import NotFoundPage from 'site/pages/NotFoundPage';

export default function ErrorPage() {
  const error = useRouteError();
  const notFound = isRouteErrorResponse(error) && error.status === 404;

  useReportRouteError(error);
  usePageTitle('Hiba történt');

  if (notFound) return <NotFoundPage />;

  return (
    <NoSignal
      actions={
        <>
          <Button onClick={() => window.location.reload()} size="lg">
            <RotateCwIcon data-icon="inline-start" />
            Újratöltés
          </Button>
          <Button
            asChild
            className="border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white dark:border-white/20 dark:bg-transparent dark:hover:bg-white/10"
            size="lg"
            variant="outline"
          >
            <Link to="/">
              <HouseIcon data-icon="inline-start" />
              Kezdőlap
            </Link>
          </Button>
        </>
      }
      code="500 · Adáshiba"
      title="Valami félresikerült"
    >
      Váratlan hiba történt. Próbáld újra, és ha továbbra sem működik, írj
      nekünk az{' '}
      <a
        className="text-white underline underline-offset-4"
        href="mailto:info@bsstudio.hu"
      >
        info@bsstudio.hu
      </a>{' '}
      címre.
    </NoSignal>
  );
}
