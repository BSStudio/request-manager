import type { ReactNode } from 'react';

import PageHero from 'site/components/PageHero';

type LegalDocumentProps = {
  children: ReactNode;
  title: string;
};

export default function LegalDocument({ children, title }: LegalDocumentProps) {
  return (
    <>
      <PageHero kicker="Jogi tudnivalók" title={title}>
        <p className="mt-4 max-w-xl text-lg text-white/70">
          A dokumentum csak angolul érhető el.
        </p>
      </PageHero>
      <div className="relative z-10 mx-auto -mt-16 w-full max-w-6xl px-4 pb-24 sm:px-6">
        <article
          className="max-w-3xl rounded-3xl border bg-card p-6 leading-relaxed text-card-foreground/90 shadow-sm sm:p-10 [&_a]:text-primary [&_a]:underline [&_a]:underline-offset-4 [&_h2]:mt-10 [&_h2]:text-2xl [&_h2]:font-bold [&_h2]:text-foreground [&_h2:first-child]:mt-0 [&_h3]:mt-8 [&_h3]:text-lg [&_h3]:font-semibold [&_h3]:text-foreground [&_li]:mt-2 [&_li]:pl-1 [&_ol]:mt-4 [&_ol]:pl-6 [&_ol_ol]:mt-2 [&_p]:mt-4 [&_strong]:text-foreground [&_ul]:mt-4 [&_ul]:list-disc [&_ul]:pl-6"
          lang="en"
        >
          {children}
        </article>
      </div>
    </>
  );
}
