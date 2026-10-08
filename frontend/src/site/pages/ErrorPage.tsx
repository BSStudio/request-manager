import { useState } from 'react';

import { cn } from 'cn';
import { HouseIcon, Loader2Icon, RotateCwIcon, SendIcon } from 'lucide-react';
import { isRouteErrorResponse, Link, useRouteError } from 'react-router';

import { usePageTitle } from 'hooks/usePageTitle';
import { useReportRouteError } from 'hooks/useReportRouteError';
import NoSignal from 'site/components/NoSignal';
import { Button } from 'site/components/ui/button';
import { Textarea } from 'site/components/ui/textarea';
import NotFoundPage from 'site/pages/NotFoundPage';

const outlineOnInk =
  'border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white dark:border-white/20 dark:bg-transparent dark:hover:bg-white/10';

export default function ErrorPage() {
  const error = useRouteError();
  const notFound = isRouteErrorResponse(error) && error.status === 404;
  const [message, setMessage] = useState('');

  const { feedback, reported } = useReportRouteError(error);
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
          <Button asChild className={outlineOnInk} size="lg" variant="outline">
            <Link to="/">
              <HouseIcon data-icon="inline-start" />
              Kezdőlap
            </Link>
          </Button>
        </>
      }
      code="500 · Adáshiba"
      footer={
        reported &&
        (feedback.isSuccess ? (
          <p className="text-sm text-white/70">
            Köszönjük, hogy segítesz kijavítani a hibát!
          </p>
        ) : (
          <form
            className="text-left"
            onSubmit={(event) => {
              event.preventDefault();
              if (message.trim()) feedback.mutate(message.trim());
            }}
          >
            <label className="text-sm font-medium" htmlFor="crash-feedback">
              Mit csináltál, amikor a hiba történt?
            </label>
            <p className="mt-1 text-sm text-white/60" id="crash-feedback-hint">
              Ha leírod, könnyebben megtaláljuk és kijavítjuk.
            </p>
            <Textarea
              aria-describedby="crash-feedback-hint"
              className="mt-3 resize-none border-white/20 dark:bg-white/5"
              id="crash-feedback"
              onChange={(event) => setMessage(event.target.value)}
              readOnly={feedback.isPending}
              rows={3}
              value={message}
            />
            {feedback.isError && (
              <p className="mt-2 text-sm text-destructive" role="alert">
                Nem sikerült elküldeni. Próbáld újra!
              </p>
            )}
            <Button
              className={cn('mt-3 w-full', outlineOnInk)}
              disabled={feedback.isPending || !message.trim()}
              type="submit"
              variant="outline"
            >
              {feedback.isPending ? (
                <Loader2Icon
                  className="animate-spin"
                  data-icon="inline-start"
                />
              ) : (
                <SendIcon data-icon="inline-start" />
              )}
              Küldés
            </Button>
          </form>
        ))
      }
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
