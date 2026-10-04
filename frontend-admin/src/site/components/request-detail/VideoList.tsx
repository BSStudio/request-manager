import { useQuery } from '@tanstack/react-query';
import { cn } from 'cn';
import { ArrowUpRightIcon, FilmIcon, PlayIcon } from 'lucide-react';

import DetailCard from 'site/components/request-detail/DetailCard';
import StatusBadge from 'site/components/StatusBadge';
import { Button } from 'site/components/ui/button';
import { Skeleton } from 'site/components/ui/skeleton';
import { requestVideosQuery } from 'site/lib/queries';
import { getRequestStep, getVideoStatus } from 'site/lib/requestStatus';

type VideoListProps = {
  requestId: number;
  status: number;
};

export default function VideoList({ requestId, status }: VideoListProps) {
  const { data, isError, isPending } = useQuery(requestVideosQuery(requestId));
  const step = getRequestStep(status);

  if (step === null && !data?.length) return null;

  const videos = [...(data ?? [])].sort((a, b) => a.id - b.id);

  return (
    <DetailCard title="Videók">
      {isPending && (
        <div className="flex items-center gap-4">
          <Skeleton className="size-12 rounded-xl" />
          <Skeleton className="h-5 w-1/2" />
        </div>
      )}
      {isError && (
        <p className="text-sm text-muted-foreground">
          Nem sikerült betölteni a videókat. Próbáld újra később!
        </p>
      )}
      {data?.length === 0 && (
        <p className="text-sm text-muted-foreground">
          {step !== null && step < 2
            ? 'Az esemény után itt találod majd az elkészült videókat.'
            : 'Hamarosan itt lesznek a videók.'}
        </p>
      )}
      {videos.length > 0 && (
        <ul className="divide-y">
          {videos.map((video) => (
            <li
              className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
              key={video.id}
            >
              <span
                className={cn(
                  'grid size-12 shrink-0 place-items-center rounded-xl',
                  video.video_url
                    ? 'bg-primary/10 text-primary'
                    : 'bg-muted text-muted-foreground',
                )}
              >
                {video.video_url ? (
                  <PlayIcon className="size-5" />
                ) : (
                  <FilmIcon className="size-5" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-medium">{video.title}</p>
                <StatusBadge
                  className="mt-1.5"
                  status={getVideoStatus(video.status)}
                />
              </div>
              {video.video_url && (
                <Button
                  asChild
                  className="max-sm:w-8 max-sm:px-0"
                  size="sm"
                  variant="outline"
                >
                  <a href={video.video_url} rel="noreferrer" target="_blank">
                    <span className="max-sm:sr-only">Megnézem</span>
                    <ArrowUpRightIcon />
                  </a>
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </DetailCard>
  );
}
