import { useEffect } from 'react';

const siteTitle = 'Felkéréskezelő | Budavári Schönherz Stúdió';

export function usePageTitle(title?: string) {
  useEffect(() => {
    document.title = title ? `${title} | ${siteTitle}` : siteTitle;
  }, [title]);
}
