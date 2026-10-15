import { initSentry } from 'helpers/initSentry';
import { isAdminPath } from 'helpers/isAdminPath';
import 'helpers/pwa';

// Only one app is loaded per page, so the global CSS of PrimeReact and
// Tailwind never meet. Links between the two apps reload the page. Sentry
// starts first, because it only instruments routers created after it, and
// each app creates its router as its modules load.
if (isAdminPath(window.location.pathname)) {
  initSentry('admin');
  void import('./admin/main');
} else {
  initSentry('site');
  void import('./site/main');
}
