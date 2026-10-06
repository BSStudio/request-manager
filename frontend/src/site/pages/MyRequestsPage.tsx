import { useQuery } from '@tanstack/react-query';
import { format, isBefore, startOfToday } from 'date-fns';
import { hu } from 'date-fns/locale';
import {
  ArrowRightIcon,
  ChevronRightIcon,
  ClapperboardIcon,
  PlusIcon,
} from 'lucide-react';
import { Link } from 'react-router';

import type { RequestList } from 'api/models';
import { usePageTitle } from 'hooks/usePageTitle';
import LoadError from 'site/components/LoadError';
import PageHero from 'site/components/PageHero';
import StatusBadge from 'site/components/StatusBadge';
import { Button } from 'site/components/ui/button';
import { Skeleton } from 'site/components/ui/skeleton';
import { formatTime } from 'site/lib/dates';
import { myRequestsQuery } from 'site/lib/queries';
import { getRequestStatus } from 'site/lib/requestStatus';

function RequestRow({ request }: { request: RequestList }) {
  const start = new Date(request.start_datetime);
  const status = getRequestStatus(request.status);

  return (
    <li>
      <Link
        className="group flex items-center gap-4 px-5 py-4 transition-colors outline-none hover:bg-muted/40 focus-visible:bg-muted/40 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset sm:px-6"
        to={`/my-requests/${request.id}`}
      >
        <div className="flex w-14 shrink-0 flex-col items-center rounded-xl border bg-background py-1.5">
          <span className="font-mono text-[0.6875rem] tracking-widest text-primary uppercase">
            {format(start, 'LLL', { locale: hu }).replace('.', '')}
          </span>
          <span className="font-heading text-2xl leading-none font-bold">
            {format(start, 'd')}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold">{request.title}</p>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {format(start, 'yyyy. MMMM d.', { locale: hu })}
            <span className="max-sm:hidden">
              , {format(start, 'EEEE', { locale: hu })}
            </span>{' '}
            · {formatTime(start)}
          </p>
          <StatusBadge className="mt-2 sm:hidden" status={status} />
        </div>
        <StatusBadge className="hidden sm:inline-flex" status={status} />
        <ChevronRightIcon className="size-5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
      </Link>
    </li>
  );
}

function RequestGroup({
  requests,
  title,
}: {
  requests: RequestList[];
  title: string;
}) {
  if (!requests.length) return null;

  return (
    <section className="border-b last:border-b-0">
      <h2 className="flex items-center gap-2 px-5 pt-6 pb-2 font-mono text-xs font-normal tracking-[0.2em] text-muted-foreground uppercase sm:px-6">
        {title}
        <span className="rounded-full bg-muted px-2 py-0.5 tracking-normal">
          {requests.length}
        </span>
      </h2>
      <ul className="divide-y">
        {requests.map((request) => (
          <RequestRow key={request.id} request={request} />
        ))}
      </ul>
    </section>
  );
}

function LoadingRows() {
  return (
    <div aria-busy className="divide-y pt-6">
      {[0, 1, 2].map((index) => (
        <div className="flex items-center gap-4 px-5 py-4 sm:px-6" key={index}>
          <Skeleton className="h-15 w-14 rounded-xl" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-2/3 max-w-72" />
            <Skeleton className="h-4 w-1/2 max-w-56" />
          </div>
        </div>
      ))}
    </div>
  );
}

function MyRequestsPage() {
  usePageTitle('Felkéréseim');
  const { data, isError, isPending, isRefetching, refetch } =
    useQuery(myRequestsQuery());

  const today = startOfToday();
  // The API sorts by start, latest first. Upcoming ones read soonest first.
  const upcoming = (data ?? [])
    .filter((request) => !isBefore(new Date(request.start_datetime), today))
    .reverse();
  const past = (data ?? []).filter((request) =>
    isBefore(new Date(request.start_datetime), today),
  );

  return (
    <>
      <PageHero
        actions={
          // From md up the header has the same button.
          <Button
            asChild
            className="bg-white text-ink hover:bg-white/85 md:hidden"
            size="lg"
          >
            <Link to="/new-request">
              <PlusIcon data-icon="inline-start" />
              Új felkérés
            </Link>
          </Button>
        }
        kicker="Felkéréseim"
        title="Hol tart a felkérésed?"
      >
        <p className="mt-4 max-w-xl text-lg text-white/70">
          Itt követheted, hogyan haladunk a felkéréseiddel, és itt találod az
          elkészült videókat is.
        </p>
      </PageHero>
      <div className="relative z-10 mx-auto -mt-16 w-full max-w-6xl px-4 pb-24 sm:px-6">
        <div className="overflow-hidden rounded-3xl border bg-card shadow-sm">
          {isPending && <LoadingRows />}
          {isError && (
            <LoadError
              onRetry={() => void refetch()}
              retrying={isRefetching}
              title="Nem sikerült betölteni a felkéréseidet."
            />
          )}
          {data?.length === 0 && (
            <div className="flex flex-col items-center px-6 py-20 text-center">
              <span className="grid size-16 place-items-center rounded-full bg-primary/10 text-primary">
                <ClapperboardIcon className="size-7" />
              </span>
              <h2 className="mt-6 text-2xl font-bold">
                Még nem küldtél be felkérést
              </h2>
              <p className="mt-2 max-w-sm text-muted-foreground">
                Ha szeretnéd, hogy forgassunk vagy élőben közvetítsünk az
                eseményeden, néhány pillanat alatt beküldheted a felkérésedet.
              </p>
              <Button asChild className="mt-8" size="lg">
                <Link to="/new-request">
                  Felkérés beküldése
                  <ArrowRightIcon data-icon="inline-end" />
                </Link>
              </Button>
            </div>
          )}
          {!!data?.length && (
            <>
              <RequestGroup requests={upcoming} title="Közelgő" />
              <RequestGroup requests={past} title="Korábbi" />
            </>
          )}
        </div>
      </div>
    </>
  );
}

export { MyRequestsPage as Component };
