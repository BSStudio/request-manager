import React from 'react';

import { ScrollTop } from 'primereact/scrolltop';
import { Outlet, ScrollRestoration, useNavigation } from 'react-router';

import AppStatus from 'components/AppStatus';
import Header from 'components/Header/Header';
import LoadingPage from 'pages/LoadingPage';
import { AuthenticationProvider } from 'providers/AuthenticationProvider';

type LayoutProps = {
  children?: React.JSX.Element;
};

const Layout = ({ children }: LayoutProps) => {
  const navigation = useNavigation();

  return (
    <AuthenticationProvider>
      <div className="flex flex-column min-h-screen surface-ground">
        <Header />
        {navigation.state == 'loading' ? (
          <LoadingPage />
        ) : (
          (children ?? <Outlet />)
        )}
        <AppStatus />
        <ScrollTop threshold={200} />
        <ScrollRestoration />
      </div>
    </AuthenticationProvider>
  );
};

export default Layout;
