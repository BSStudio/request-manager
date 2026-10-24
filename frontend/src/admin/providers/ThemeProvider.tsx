import React, { lazy, Suspense } from 'react';

import { useTheme } from 'admin/hooks/useTheme';

const DarkTheme = lazy(() => import('admin/themes/dark/DarkTheme'));
const LightTheme = lazy(() => import('admin/themes/light/LightTheme'));

type ThemeProviderProps = {
  children: React.JSX.Element;
};

export const ThemeProvider = ({ children }: ThemeProviderProps) => {
  const [darkMode] = useTheme();

  // The children stay outside the Suspense: a boundary that delays their
  // commit makes RouterProvider subscribe too late and miss the first route.
  return (
    <>
      <Suspense fallback={<span />}>
        {darkMode ? <DarkTheme /> : <LightTheme />}
      </Suspense>
      {children}
    </>
  );
};
