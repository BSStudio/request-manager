import { Suspense, lazy } from 'react';

import { useSuspenseQuery } from '@tanstack/react-query';
import { ProgressBar } from 'primereact/progressbar';
import {
  type LoaderFunctionArgs,
  type ShouldRevalidateFunctionArgs,
  useLoaderData,
  useSearchParams,
} from 'react-router';

import { usersRetrieveQuery } from 'admin/api/queries';
import LastUpdatedAt from 'admin/components/LastUpdatedAt/LastUpdatedAt';
import NavigationButton from 'admin/components/UserProfile/NavigationButton';
import { queryClient } from 'api/queryClient';
import { formatName } from 'helpers/names';

const BanSection = lazy(
  () => import('admin/components/UserProfile/BanSection'),
);
const ProfileSection = lazy(
  () => import('admin/components/UserProfile/ProfileSection'),
);
const WorkedOnSection = lazy(
  () => import('admin/components/UserProfile/WorkedOnSection'),
);

const sections = [
  { icon: 'pi pi-user', name: 'profile', text: 'Profil' },
  { icon: 'pi pi-ban', name: 'ban', text: 'Kitiltás' },
  { icon: 'pi pi-list', name: 'workedOn', text: 'Anyagok' },
] as const;

export type loaderData = Awaited<ReturnType<typeof loader>>;

export async function loader({ params }: LoaderFunctionArgs) {
  if (!params.userId) {
    throw new Error('No user ID provided');
  }
  const user = await queryClient.query({
    ...usersRetrieveQuery(params.userId),
    staleTime: 'static',
  });
  return {
    userFullName: formatName(user.last_name, user.first_name),
    userId: params.userId,
  };
}

// The loader does not read the search, which only picks the section.
export function shouldRevalidate({
  currentUrl,
  defaultShouldRevalidate,
  nextUrl,
}: ShouldRevalidateFunctionArgs) {
  if (
    currentUrl.pathname === nextUrl.pathname &&
    currentUrl.search !== nextUrl.search
  ) {
    return false;
  }
  return defaultShouldRevalidate;
}

const UserProfilePage = () => {
  const [searchParams] = useSearchParams();
  const section =
    sections.find(({ name }) => name === searchParams.get('section'))?.name ??
    'profile';
  const { userId } = useLoaderData<typeof loader>();

  const { data, dataUpdatedAt, refetch } = useSuspenseQuery(
    usersRetrieveQuery(userId),
  );

  return (
    <div className="lg:px-8 md:px-6 px-4 py-5 surface-ground">
      <div className="flex flex-column lg:flex-row p-fluid">
        <ul className="border-round flex flex-row h-full justify-content-evenly lg:flex-column lg:justify-content-start lg:mb-0 lg:mr-5 list-none m-0 mb-5 md:justify-content-between shadow-2 surface-card p-0">
          {sections.map(({ icon, name, text }) => (
            <NavigationButton
              active={section === name}
              icon={icon}
              key={name}
              section={name}
              text={text}
            />
          ))}
        </ul>
        <div className="flex-auto">
          <div className="border-round shadow-2 surface-card p-5">
            <Suspense fallback={<ProgressBar mode="indeterminate" />}>
              {section === 'ban' && (
                <BanSection banData={data.ban} userId={data.id} />
              )}
              {section === 'profile' && <ProfileSection userData={data} />}
              {section === 'workedOn' && <WorkedOnSection userId={data.id} />}
            </Suspense>
          </div>
          {section !== 'workedOn' && (
            <LastUpdatedAt
              lastUpdatedAt={new Date(dataUpdatedAt)}
              refetch={refetch}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export { UserProfilePage as Component };
