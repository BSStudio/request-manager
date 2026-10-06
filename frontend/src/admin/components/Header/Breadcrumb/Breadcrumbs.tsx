import { Fragment } from 'react';

import { useIsFetching } from '@tanstack/react-query';
import { ProgressSpinner } from 'primereact/progressspinner';
import {
  href,
  Link,
  type UIMatch,
  useMatches,
  useRouteError,
} from 'react-router';

type BreadcrumbsType = {
  name: string;
  path: string;
}[];

type CrumbHandle =
  | {
      crumb: (loaderData?: unknown) => string;
    }
  | undefined;

type ReactRouterUseMatchesType = UIMatch<unknown, CrumbHandle>[];

const Breadcrumbs = () => {
  const error = useRouteError();
  const isFetching = useIsFetching();
  const matchesHook = useMatches() as ReactRouterUseMatchesType;
  const matches = error ? [] : matchesHook;

  const breadcrumbs: BreadcrumbsType = matches
    // first get rid of any matches that don't have handle and crumb
    .filter((match) => Boolean(match.handle?.crumb))
    // now map them into an array of elements, passing the loader
    // data to each one
    .map((match) => {
      return {
        name: match.handle?.crumb(match.loaderData) || '',
        path: match.pathname,
      };
    });

  return (
    <ul className="align-items-center border-bottom-1 border-top-1 flex font-medium list-none m-0 overflow-x-auto px-3 py-3 sm:px-5 surface-border surface-card">
      {/* Home button */}
      <li className="pr-3">
        <Link className="cursor-pointer no-underline" to={href('/')}>
          <i className="pi pi-home text-blue-500"></i>
        </Link>
      </li>

      {breadcrumbs.map((breadcrumb, index, array) => (
        <Fragment key={`breadcrumb-fragment-${index}`}>
          {/* Right arrow (>) */}
          <li className="px-2">
            <i className="pi pi-angle-right text-500"></i>
          </li>

          {/* Texts - Last item different, no redirect */}
          <li className="px-2">
            {!Object.is(array.length - 1, index) ? (
              <Link
                className="cursor-pointer no-underline text-blue-500 white-space-nowrap"
                to={href(breadcrumb.path)}
              >
                {breadcrumb.name}
              </Link>
            ) : (
              <span className="text-900 white-space-nowrap">
                {breadcrumb.name}
              </span>
            )}
          </li>
        </Fragment>
      ))}
      {/* Spinner indicator for network activity */}
      {!!isFetching && (
        <ProgressSpinner
          style={{
            height: '1.25rem',
            marginLeft: '1rem',
            width: '1.25rem',
          }}
        />
      )}
    </ul>
  );
};

export default Breadcrumbs;
