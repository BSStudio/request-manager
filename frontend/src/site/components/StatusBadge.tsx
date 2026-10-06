import { cn } from 'cn';

import type { StatusInfo, StatusTone } from 'site/lib/requestStatus';

const toneClasses: Record<StatusTone, string> = {
  active: 'border-primary/30 bg-primary/10 text-primary',
  done: 'border-success/30 bg-success/10 text-success',
  failed: 'border-destructive/30 bg-destructive/10 text-destructive',
  inactive: 'border-border bg-muted text-muted-foreground',
  pending: 'border-warning/30 bg-warning/10 text-warning',
};

type StatusBadgeProps = {
  className?: string;
  status: StatusInfo;
};

export default function StatusBadge({ className, status }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap',
        toneClasses[status.tone],
        className,
      )}
    >
      <span aria-hidden className="size-1.5 rounded-full bg-current" />
      {status.label}
    </span>
  );
}
