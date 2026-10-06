import { cn } from 'cn';
import { RefreshCwIcon } from 'lucide-react';

import { Button } from 'site/components/ui/button';

type LoadErrorProps = {
  className?: string;
  onRetry: () => void;
  retrying: boolean;
  title: string;
};

export default function LoadError({
  className,
  onRetry,
  retrying,
  title,
}: LoadErrorProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center px-6 py-16 text-center',
        className,
      )}
    >
      <p className="font-semibold">{title}</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Ellenőrizd az internetkapcsolatodat, és próbáld újra!
      </p>
      <Button
        className="mt-6"
        disabled={retrying}
        onClick={onRetry}
        variant="outline"
      >
        <RefreshCwIcon
          className={retrying ? 'animate-spin' : undefined}
          data-icon="inline-start"
        />
        Újrapróbálom
      </Button>
    </div>
  );
}
