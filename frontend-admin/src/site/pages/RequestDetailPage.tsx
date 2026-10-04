import { useEffect } from 'react';

import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { hu } from 'date-fns/locale';
import {
  ArrowLeftIcon,
  CalendarDaysIcon,
  ClapperboardIcon,
  MapPinIcon,
  RefreshCwIcon,
} from 'lucide-react';
import { Link, useParams } from 'react-router';

import PageHero from 'site/components/PageHero';
import DetailCard from 'site/components/request-detail/DetailCard';
import PersonContact from 'site/components/request-detail/PersonContact';
import RequestProgress from 'site/components/request-detail/RequestProgress';
import VideoList from 'site/components/request-detail/VideoList';
import StatusBadge from 'site/components/StatusBadge';
import { Button } from 'site/components/ui/button';
import { Skeleton } from 'site/components/ui/skeleton';
import { usePageTitle } from 'site/hooks/usePageTitle';
import { isNotFound } from 'site/lib/apiError';
import { formatRange } from 'site/lib/dates';
import { requestQuery } from 'site/lib/queries';
import { getRequestStatus, getRequestStep } from 'site/lib/requestStatus';
import { useSessionUser } from 'site/lib/session';
import NotFoundPage from 'site/pages/NotFoundPage';

const backLink = (
  <Link
    className="inline-flex items-center gap-2 transition-colors hover:text-white"
    to="/my-requests"
  >
    <ArrowLeftIcon className="size-3.5" />
    Felkéréseim
  </Link>
);

function RequestDetail({ id }: { id: number }) {
  const user = useSessionUser();
  const { data, error, isError, isRefetching, refetch } = useQuery(
    requestQuery(id),
  );
  const notFound = isNotFound(error);
  // Staff open the requests of others from e-mails, those live in the admin.
  const toAdmin = notFound && !!user?.isPrivileged;

  usePageTitle(data?.title);

  useEffect(() => {
    if (toAdmin) window.location.replace(`/admin/requests/${id}`);
  }, [id, toAdmin]);

  if (toAdmin) return null;
  if (notFound) return <NotFoundPage />;

  if (isError) {
    return (
      <>
        <PageHero kicker={backLink} title="Hoppá" />
        <div className="relative z-10 mx-auto -mt-16 w-full max-w-6xl px-4 pb-24 sm:px-6">
          <div className="flex flex-col items-center rounded-3xl border bg-card px-6 py-16 text-center shadow-sm">
            <p className="font-semibold">Nem sikerült betölteni a felkérést.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Ellenőrizd az internetkapcsolatodat, és próbáld újra!
            </p>
            <Button
              className="mt-6"
              disabled={isRefetching}
              onClick={() => void refetch()}
              variant="outline"
            >
              <RefreshCwIcon
                className={isRefetching ? 'animate-spin' : undefined}
                data-icon="inline-start"
              />
              Újrapróbálom
            </Button>
          </div>
        </div>
      </>
    );
  }

  const status = data && getRequestStatus(data.status);
  const showRequestedBy =
    data?.requested_by && data.requested_by.id !== data.requester.id;

  return (
    <>
      <PageHero
        kicker={backLink}
        title={
          data?.title ?? (
            <span className="block h-[1.2em] w-full max-w-md animate-pulse rounded-xl bg-white/10" />
          )
        }
      >
        {data && status ? (
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 text-white/75">
            <StatusBadge status={status} />
            <span className="inline-flex items-center gap-2">
              <CalendarDaysIcon className="size-4 shrink-0 text-white/50" />
              {formatRange(
                new Date(data.start_datetime),
                new Date(data.end_datetime),
              )}
            </span>
            <span className="inline-flex items-center gap-2">
              <MapPinIcon className="size-4 shrink-0 text-white/50" />
              {data.place}
            </span>
            <span className="inline-flex items-center gap-2">
              <ClapperboardIcon className="size-4 shrink-0 text-white/50" />
              {data.type}
            </span>
          </div>
        ) : (
          <div className="mt-6 h-6 w-full max-w-lg animate-pulse rounded-lg bg-white/10" />
        )}
      </PageHero>
      <div className="relative z-10 mx-auto -mt-16 grid w-full max-w-6xl items-start gap-6 px-4 pb-24 sm:px-6 lg:grid-cols-[1fr_20rem] lg:gap-8">
        {data ? (
          <>
            <div className="min-w-0 space-y-6">
              <DetailCard title="Állapot">
                <RequestProgress status={data.status} />
              </DetailCard>
              <VideoList requestId={data.id} status={data.status} />
            </div>
            <aside className="space-y-6 lg:sticky lg:top-24">
              {data.responsible && (
                <DetailCard title="Kapcsolattartód">
                  <PersonContact person={data.responsible} />
                </DetailCard>
              )}
              {!data.responsible && getRequestStep(data.status) === 0 && (
                <DetailCard title="Kapcsolattartód">
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    Ha elvállaljuk a felkérést, itt látod majd, ki foglalkozik
                    vele.
                  </p>
                </DetailCard>
              )}
              <DetailCard title="Felkérő">
                <PersonContact person={data.requester} />
                <dl className="mt-5 space-y-1 border-t pt-5 text-sm">
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">Beküldve</dt>
                    <dd>
                      {format(new Date(data.created), 'yyyy. MMM d. HH:mm', {
                        locale: hu,
                      })}
                    </dd>
                  </div>
                  {showRequestedBy && (
                    <div className="flex justify-between gap-4">
                      <dt className="text-muted-foreground">Beküldte</dt>
                      <dd className="text-right">
                        {data.requested_by.full_name}
                      </dd>
                    </div>
                  )}
                </dl>
              </DetailCard>
            </aside>
          </>
        ) : (
          <>
            <Skeleton className="h-56 rounded-3xl" />
            <Skeleton className="h-56 rounded-3xl" />
          </>
        )}
      </div>
    </>
  );
}

function RequestDetailPage() {
  const id = Number(useParams().id);

  if (!Number.isInteger(id) || id <= 0) return <NotFoundPage />;
  return <RequestDetail id={id} key={id} />;
}

export { RequestDetailPage as Component };
