import { cn } from 'cn';
import { CheckIcon } from 'lucide-react';

export type StepInfo = {
  description: string;
  title: string;
};

type StepIndicatorProps = {
  current: number;
  onSelect: (index: number) => void;
  steps: StepInfo[];
};

export function StepList({ current, onSelect, steps }: StepIndicatorProps) {
  return (
    <ol aria-label="Lépések">
      {steps.map(({ description, title }, index) => {
        const done = index < current;
        const active = index === current;

        return (
          <li className="relative pb-8 last:pb-0" key={title}>
            {index < steps.length - 1 && (
              <span
                aria-hidden
                className={cn(
                  'absolute top-11 bottom-1 left-5 w-px',
                  done ? 'bg-primary' : 'bg-border',
                )}
              />
            )}
            <button
              aria-current={active ? 'step' : undefined}
              className="group flex w-full items-start gap-4 text-left disabled:cursor-default"
              disabled={!done}
              onClick={() => onSelect(index)}
              type="button"
            >
              <span
                className={cn(
                  'grid size-10 shrink-0 place-items-center rounded-full border font-mono text-sm transition-colors',
                  done &&
                    'border-primary bg-primary text-primary-foreground group-hover:bg-primary/85',
                  active &&
                    'border-primary bg-background text-primary ring-4 ring-primary/15',
                  !done && !active && 'bg-background text-muted-foreground',
                )}
              >
                {done ? (
                  <CheckIcon className="size-4.5" />
                ) : (
                  String(index + 1).padStart(2, '0')
                )}
              </span>
              <span className="pt-1">
                <span
                  className={cn(
                    'block font-medium',
                    !done && !active && 'text-muted-foreground',
                  )}
                >
                  {title}
                </span>
                <span className="mt-0.5 block text-sm text-muted-foreground">
                  {description}
                </span>
              </span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}

export function StepProgress({
  current,
  steps,
}: Omit<StepIndicatorProps, 'onSelect'>) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex flex-1 gap-1.5">
        {steps.map(({ title }, index) => (
          <span
            className={cn(
              'h-1.5 flex-1 rounded-full transition-colors',
              index <= current ? 'bg-primary' : 'bg-muted',
            )}
            key={title}
          />
        ))}
      </div>
      <p className="font-mono text-sm text-muted-foreground">
        {current + 1}/{steps.length}
      </p>
    </div>
  );
}
