import type { ReactNode } from 'react';

import { cn } from 'cn';

type DetailCardProps = {
  children: ReactNode;
  className?: string;
  title: string;
};

export default function DetailCard({
  children,
  className,
  title,
}: DetailCardProps) {
  return (
    <section
      className={cn(
        'rounded-3xl border bg-card p-6 shadow-sm sm:p-8',
        className,
      )}
    >
      <h2 className="font-mono text-xs font-normal tracking-[0.2em] text-muted-foreground uppercase">
        {title}
      </h2>
      <div className="mt-5">{children}</div>
    </section>
  );
}
