import { useState } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2Icon, PencilIcon, Trash2Icon } from 'lucide-react';
import { toast } from 'sonner';

import { requestsApi } from 'api/http';
import type { RatingRetrieve, VideoListRetrieve } from 'api/models';
import StarRating from 'site/components/StarRating';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from 'site/components/ui/alert-dialog';
import { Button } from 'site/components/ui/button';
import { Field, FieldDescription, FieldLabel } from 'site/components/ui/field';
import { Textarea } from 'site/components/ui/textarea';
import { getApiErrorMessage } from 'site/lib/apiError';
import { requestVideosQuery } from 'site/lib/queries';

type Draft = { rating: number; review: string };

type VideoRatingProps = {
  requestId: number;
  video: VideoListRetrieve;
};

export default function VideoRating({ requestId, video }: VideoRatingProps) {
  const queryClient = useQueryClient();
  // An unrated video comes with an empty object.
  const rating = video.rating.rating ? video.rating : null;
  const [draft, setDraft] = useState<Draft | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const updateCache = (next: RatingRetrieve | null) =>
    queryClient.setQueryData(requestVideosQuery(requestId).queryKey, (videos) =>
      videos?.map((item) =>
        item.id === video.id
          ? { ...item, rating: next ?? ({} as RatingRetrieve) }
          : item,
      ),
    );

  const save = useMutation({
    mutationFn: async (values: Draft) => {
      const { data } = rating
        ? await requestsApi.requestsVideosRatingPartialUpdate(
            requestId,
            video.id,
            values,
          )
        : await requestsApi.requestsVideosRatingCreate(
            requestId,
            video.id,
            values,
          );
      return { created: !rating, data };
    },
    onError: (error) =>
      toast.error('Nem sikerült menteni az értékelést.', {
        description: getApiErrorMessage(error),
      }),
    onSuccess: ({ created, data }) => {
      updateCache({ ...data, review: data.review ?? '' });
      setDraft(null);
      if (created) toast.success('Köszönjük az értékelést!');
    },
  });

  const remove = useMutation({
    mutationFn: () =>
      requestsApi.requestsVideosRatingDestroy(requestId, video.id),
    onError: (error) =>
      toast.error('Nem sikerült törölni az értékelést.', {
        description: getApiErrorMessage(error),
      }),
    onSuccess: () => {
      updateCache(null);
      setConfirmingDelete(false);
    },
  });

  const busy = save.isPending || remove.isPending;
  const startDraft = (stars: number) =>
    setDraft({ rating: stars, review: draft?.review ?? rating?.review ?? '' });

  return (
    <div className="mt-4 rounded-2xl border bg-muted/30 p-4 sm:ml-16">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        <p className="text-sm font-medium">
          {rating ? 'Az értékelésed' : 'Hogy tetszett a videó?'}
        </p>
        <StarRating
          disabled={busy}
          onChange={startDraft}
          value={draft?.rating ?? rating?.rating ?? 0}
        />
      </div>
      {draft && (
        <form
          className="mt-4"
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate({ ...draft, review: draft.review.trim() });
          }}
        >
          <Field>
            <FieldLabel htmlFor={`review-${video.id}`}>Véleményed</FieldLabel>
            <Textarea
              id={`review-${video.id}`}
              onChange={(event) =>
                setDraft({ ...draft, review: event.target.value })
              }
              placeholder="Mit gondolsz a videóról és a stáb munkájáról?"
              rows={3}
              value={draft.review}
            />
            <FieldDescription>
              Nem kötelező, de sokat segít nekünk.
            </FieldDescription>
          </Field>
          <div className="mt-4 flex justify-end gap-2">
            <Button
              disabled={busy}
              onClick={() => setDraft(null)}
              size="sm"
              type="button"
              variant="ghost"
            >
              Mégsem
            </Button>
            <Button disabled={busy} size="sm" type="submit">
              {save.isPending && (
                <Loader2Icon
                  className="animate-spin"
                  data-icon="inline-start"
                />
              )}
              Mentés
            </Button>
          </div>
        </form>
      )}
      {rating && !draft && (
        <>
          {rating.review && (
            <p className="mt-3 text-sm leading-relaxed whitespace-pre-wrap text-muted-foreground">
              „{rating.review}”
            </p>
          )}
          <div className="mt-2 -mb-1 -ml-2 flex flex-wrap gap-1">
            <Button
              disabled={busy}
              onClick={() => startDraft(rating.rating)}
              size="sm"
              variant="ghost"
            >
              <PencilIcon data-icon="inline-start" />
              {rating.review ? 'Szerkesztés' : 'Írj róla pár sort'}
            </Button>
            <Button
              className="text-muted-foreground"
              disabled={busy}
              onClick={() => setConfirmingDelete(true)}
              size="sm"
              variant="ghost"
            >
              <Trash2Icon data-icon="inline-start" />
              Törlés
            </Button>
          </div>
        </>
      )}
      <AlertDialog onOpenChange={setConfirmingDelete} open={confirmingDelete}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Törlöd az értékelésed?</AlertDialogTitle>
            <AlertDialogDescription>
              {rating?.review
                ? 'A csillagok mellett a véleményed is törlődik.'
                : 'Később bármikor újra értékelheted a videót.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={remove.isPending}>
              Mégsem
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={remove.isPending}
              onClick={(event) => {
                // Stays open until the request finishes.
                event.preventDefault();
                remove.mutate();
              }}
              variant="destructive"
            >
              {remove.isPending && (
                <Loader2Icon
                  className="animate-spin"
                  data-icon="inline-start"
                />
              )}
              Törlés
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
