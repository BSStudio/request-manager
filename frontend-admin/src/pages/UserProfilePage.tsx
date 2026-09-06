import { Suspense, lazy, useState } from 'react';

import { useSuspenseQuery } from '@tanstack/react-query';
import { ProgressBar } from 'primereact/progressbar';
import { type LoaderFunctionArgs, useLoaderData } from 'react-router';

import { usersRetrieveQuery } from 'api/queries';
import LastUpdatedAt from 'components/LastUpdatedAt/LastUpdatedAt';
import NavigationButton from 'components/UserProfile/NavigationButton';
import { queryClient } from 'router';

const BanSection = lazy(() => import('components/UserProfile/BanSection'));
const ProfileSection = lazy(
  () => import('components/UserProfile/ProfileSection'),
);
const WorkedOnSection = lazy(
  () => import('components/UserProfile/WorkedOnSection'),
);

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
    userFullName: `${user.last_name} ${user.first_name}`,
    userId: params.userId,
  };
}

const UserProfilePage = () => {
  const [section, setSection] = useState<string>('profile');
  const { userId } = useLoaderData() as loaderData;

  const { data, dataUpdatedAt, refetch } = useSuspenseQuery(
    usersRetrieveQuery(userId),
  );

  return (
    <div className="lg:px-8 md:px-6 px-4 py-5 surface-ground">
      <div className="flex flex-column lg:flex-row p-fluid">
        <ul className="border-round flex flex-row h-full justify-content-evenly lg:flex-column lg:justify-content-start lg:mb-0 lg:mr-5 list-none m-0 mb-5 md:justify-content-between shadow-2 surface-card p-0">
          <NavigationButton
            icon="pi pi-user"
            onClick={() => setSection('profile')}
            text="Profil"
          />
          <NavigationButton
            icon="pi pi-ban"
            onClick={() => setSection('ban')}
            text="Kitiltás"
          />
          <NavigationButton
            icon="pi pi-list"
            onClick={() => setSection('workedOn')}
            text="Anyagok"
          />
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
