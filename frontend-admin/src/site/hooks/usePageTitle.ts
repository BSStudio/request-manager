import { useDocumentTitle } from 'hooks/useDocumentTitle';

const siteTitle = 'Felkéréskezelő | Budavári Schönherz Stúdió';

export function usePageTitle(title?: string) {
  useDocumentTitle(title ? `${title} | ${siteTitle}` : siteTitle);
}
