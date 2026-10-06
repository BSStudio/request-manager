import type { ReactNode } from 'react';

import { cn } from 'cn';

type SectionHeadingProps = {
  children?: ReactNode;
  className?: string;
  kicker: string;
  title: string;
};

export default function SectionHeading({
  children,
  className,
  kicker,
  title,
}: SectionHeadingProps) {
  return (
    <div className={cn('max-w-2xl', className)}>
      <p className="flex items-center gap-3 font-mono text-xs tracking-[0.2em] text-primary uppercase">
        <span className="h-px w-8 bg-current opacity-50" />
        {kicker}
      </p>
      <h2 className="mt-4 text-4xl font-bold sm:text-5xl">{title}</h2>
      {children && (
        <p className="mt-5 text-lg leading-relaxed text-muted-foreground">
          {children}
        </p>
      )}
    </div>
  );
}
