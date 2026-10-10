import { useQuery } from '@tanstack/react-query';

import { formatName } from 'helpers/names';
import { meQuery } from 'helpers/session';
import { usePageTitle } from 'hooks/usePageTitle';
import DetailCard from 'site/components/DetailCard';
import LoadError from 'site/components/LoadError';
import PageHero from 'site/components/PageHero';
import AvatarPicker from 'site/components/profile/AvatarPicker';
import LoginMethods from 'site/components/profile/LoginMethods';
import PersonalDetails from 'site/components/profile/PersonalDetails';
import { Skeleton } from 'site/components/ui/skeleton';
import UserAvatar from 'site/components/UserAvatar';

const roleLabels: Record<string, string> = {
  admin: 'Adminisztrátor',
  staff: 'BSS-tag',
};

function ProfilePage() {
  usePageTitle('Profilom');
  const { data: user, isError, isRefetching, refetch } = useQuery(meQuery());

  const name = user && formatName(user.last_name, user.first_name);
  const badges = user
    ? [roleLabels[user.role], ...user.groups].filter(Boolean)
    : [];

  return (
    <>
      <PageHero
        kicker="Profilom"
        media={
          user ? (
            <UserAvatar
              className="size-20 shrink-0 ring-4 ring-white/10 sm:size-32"
              user={{
                avatar: user.avatar_url,
                name: name || user.username,
              }}
            />
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
          <LoadError
            className="rounded-3xl border bg-card shadow-sm lg:col-span-2"
            onRetry={() => void refetch()}
            retrying={isRefetching}
            title="Nem sikerült betölteni a profilodat."
          />
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
