import { isAdminPath } from 'helpers/isAdminPath';

// Only one app is loaded per page, so the global CSS of PrimeReact and
// Tailwind never meet. Links between the two apps reload the page.
if (isAdminPath(window.location.pathname)) {
  void import('./admin');
} else {
  void import('./site/main');
}
