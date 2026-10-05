import { useQuery } from '@tanstack/react-query';
import { RefreshCwIcon } from 'lucide-react';

import DetailCard from 'site/components/DetailCard';
import PageHero from 'site/components/PageHero';
import AvatarPicker from 'site/components/profile/AvatarPicker';
import LoginMethods from 'site/components/profile/LoginMethods';
import PersonalDetails from 'site/components/profile/PersonalDetails';
import { Avatar, AvatarFallback, AvatarImage } from 'site/components/ui/avatar';
import { Button } from 'site/components/ui/button';
import { Skeleton } from 'site/components/ui/skeleton';
import { usePageTitle } from 'site/hooks/usePageTitle';
import { meQuery } from 'site/lib/queries';
import { getInitials } from 'site/lib/session';

const roleLabels: Record<string, string> = {
  admin: 'Adminisztrátor',
  staff: 'BSS-tag',
};

function ProfilePage() {
  usePageTitle('Profilom');
  const { data: user, isError, isRefetching, refetch } = useQuery(meQuery());

  const name =
    user && `${user.last_name ?? ''} ${user.first_name ?? ''}`.trim();
  const badges = user
    ? [roleLabels[user.role], ...user.groups].filter(Boolean)
    : [];

  return (
    <>
      <PageHero
        kicker="Profilom"
        media={
          user ? (
            <Avatar className="size-20 shrink-0 ring-4 ring-white/10 sm:size-32">
              <AvatarImage alt="" src={user.profile.avatar_url || undefined} />
              <AvatarFallback className="bg-primary text-2xl font-semibold text-primary-foreground sm:text-4xl">
                {getInitials(name || user.username)}
              </AvatarFallback>
            </Avatar>
          ) : (
            <span className="size-20 shrink-0 animate-pulse rounded-full bg-white/10 sm:size-32" />
          )
        }
        title={
          user ? (
            name || user.username
          ) : (
            <span className="block h-[1.2em] w-full max-w-sm animate-pulse rounded-xl bg-white/10" />
          )
        }
      >
        {badges.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-2">
            {badges.map((badge) => (
              <span
                className="rounded-full bg-white/10 px-3 py-1 text-xs ring-1 ring-white/15"
                key={badge}
              >
                {badge}
              </span>
            ))}
          </div>
        )}
      </PageHero>
      <div className="relative z-10 mx-auto -mt-16 grid w-full max-w-6xl items-start gap-6 px-4 pb-24 sm:px-6 lg:grid-cols-[1fr_20rem] lg:gap-8">
        {isError && !user && (
          <div className="flex flex-col items-center rounded-3xl border bg-card px-6 py-16 text-center shadow-sm lg:col-span-2">
            <p className="font-semibold">
              Nem sikerült betölteni a profilodat.
            </p>
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
        )}
        {user && (
          <>
            <div className="min-w-0 space-y-6">
              <DetailCard title="Adataid">
                <PersonalDetails user={user} />
              </DetailCard>
              <DetailCard title="Bejelentkezés">
                <LoginMethods user={user} />
              </DetailCard>
            </div>
            <aside className="space-y-6 lg:sticky lg:top-24">
              <DetailCard title="Profilkép">
                <AvatarPicker user={user} />
              </DetailCard>
            </aside>
          </>
        )}
        {!user && !isError && (
          <>
            <Skeleton className="h-96 rounded-3xl" />
            <Skeleton className="h-48 rounded-3xl" />
          </>
        )}
      </div>
    </>
  );
}

export { ProfilePage as Component };
