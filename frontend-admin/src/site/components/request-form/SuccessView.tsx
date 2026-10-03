import { ArrowRightIcon, CheckIcon, PlusIcon } from 'lucide-react';
import { Link } from 'react-router';

import { Button } from 'site/components/ui/button';

type SuccessViewProps = {
  onNewRequest: () => void;
  requestId: number | null;
};

export default function SuccessView({
  onNewRequest,
  requestId,
}: SuccessViewProps) {
  return (
    <div className="flex flex-col items-center py-10 text-center sm:py-16">
      <span className="grid size-20 animate-in place-items-center rounded-full bg-success/15 text-success duration-500 zoom-in-50">
        <CheckIcon className="size-10" strokeWidth={2.5} />
      </span>
      <h2 className="mt-8 text-3xl font-bold sm:text-4xl">
        Megkaptuk a felkérésed!
      </h2>
      <p className="mt-4 max-w-md leading-relaxed text-muted-foreground">
        Visszaigazolást küldtünk e-mailben. A hétfői gyűlésünk után jelentkezünk
        a részletekkel.
      </p>
      <div className="mt-10 flex flex-wrap justify-center gap-3">
        {requestId && (
          <Button asChild size="lg">
            <Link to={`/my-requests/${requestId}`}>
              Felkérés megtekintése
              <ArrowRightIcon data-icon="inline-end" />
            </Link>
          </Button>
        )}
        <Button onClick={onNewRequest} size="lg" variant="outline">
          <PlusIcon data-icon="inline-start" />
          Új felkérés
        </Button>
      </div>
    </div>
  );
}
