import type { ReactNode } from 'react';

import { cn } from 'cn';

type PageHeroProps = {
  actions?: ReactNode;
  children?: ReactNode;
  kicker: ReactNode;
  media?: ReactNode;
  title: ReactNode;
};

export default function PageHero({
  actions,
  children,
  kicker,
  media,
  title,
}: PageHeroProps) {
  return (
    <section className="relative isolate overflow-hidden bg-ink pt-32 pb-28 text-white sm:pt-36">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top_right,color-mix(in_oklab,var(--primary)_45%,transparent),transparent_60%)]" />
      <div className="absolute inset-0 -z-10 bg-grain opacity-[0.07] mix-blend-overlay" />
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 sm:px-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-3 font-mono text-xs tracking-[0.2em] text-white/70 uppercase">
            <span className="h-px w-8 bg-white/40" />
            {kicker}
          </div>
          <div
            className={cn(
              'mt-5 flex items-center gap-5 sm:gap-8',
              media && 'max-sm:flex-row-reverse max-sm:justify-between',
            )}
          >
            {media}
            <div className="min-w-0">
              <h1 className="text-4xl font-bold sm:text-5xl">{title}</h1>
              {children}
            </div>
          </div>
        </div>
        {actions && <div className="flex shrink-0 gap-3">{actions}</div>}
      </div>
    </section>
  );
}
