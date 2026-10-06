import { cn } from 'cn';
import { CheckIcon, InfoIcon } from 'lucide-react';

import {
  getRequestStep,
  getStoppedNotice,
  requestSteps,
} from 'site/lib/requestStatus';

export default function RequestProgress({ status }: { status: number }) {
  const step = getRequestStep(status);

  if (step === null) {
    const notice = getStoppedNotice(status);
    const Icon = notice.icon;
    return (
      <div className="flex gap-4">
        <span className="grid size-10 shrink-0 place-items-center rounded-full bg-muted text-muted-foreground">
          <Icon className="size-5" />
        </span>
        <div>
          <p className="font-semibold">{notice.title}</p>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
            {notice.text}
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <ol className="grid grid-cols-4">
        {requestSteps.map(({ title }, index) => {
          const done = index <= step;
          const current = index === step + 1;

          return (
            <li
              aria-current={current ? 'step' : undefined}
              className="relative flex flex-col items-center text-center"
              key={title}
            >
              {index > 0 && (
                <span
                  aria-hidden
                  className={cn(
                    'absolute top-5 right-1/2 -left-1/2 h-px',
                    done && 'bg-primary',
                    current && 'bg-linear-to-r from-primary to-border',
                    !done && !current && 'bg-border',
                  )}
                />
              )}
              <span
                className={cn(
                  'relative z-10 grid size-10 place-items-center rounded-full border font-mono text-sm',
                  done && 'border-primary bg-primary text-primary-foreground',
                  current &&
                    'border-primary bg-card text-primary ring-4 ring-primary/15',
                  !done && !current && 'bg-card text-muted-foreground',
                )}
              >
                {done ? (
                  <CheckIcon className="size-4.5" />
                ) : (
                  String(index + 1).padStart(2, '0')
                )}
              </span>
              <span
                className={cn(
                  'mt-3 text-xs font-medium sm:text-sm',
                  !done && !current && 'text-muted-foreground',
                )}
              >
                {title}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="mt-6 flex gap-3 rounded-2xl bg-muted/50 px-4 py-3 text-sm leading-relaxed">
        <InfoIcon className="mt-0.5 size-4 shrink-0 text-primary" />
        {requestSteps[step].text}
      </p>
    </>
  );
}
