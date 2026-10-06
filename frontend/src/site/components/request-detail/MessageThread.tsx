import { useRef, useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2Icon, MessagesSquareIcon, SendIcon } from 'lucide-react';
import { toast } from 'sonner';

import { getApiErrorMessage, isRateLimited } from 'api/errors';
import { requestsApi } from 'api/http';
import DetailCard from 'site/components/DetailCard';
import Message from 'site/components/request-detail/Message';
import { Button } from 'site/components/ui/button';
import { Skeleton } from 'site/components/ui/skeleton';
import { Textarea } from 'site/components/ui/textarea';
import { requestCommentsQuery } from 'site/lib/queries';
import { useSessionUser } from 'site/lib/session';

export default function MessageThread({ requestId }: { requestId: number }) {
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const { data, isError, isPending } = useQuery(
    requestCommentsQuery(requestId),
  );
  const [text, setText] = useState('');
  const list = useRef<HTMLOListElement>(null);

  const send = useMutation({
    mutationFn: async (message: string) =>
      (await requestsApi.requestsCommentsCreate(requestId, { text: message }))
        .data,
    onError: (error) =>
      toast.error('Nem sikerült elküldeni az üzenetet.', {
        description: isRateLimited(error)
          ? 'Túl sok üzenetet küldtél. Próbáld újra később!'
          : getApiErrorMessage(error),
      }),
    onSuccess: (message) => {
      queryClient.setQueryData(
        requestCommentsQuery(requestId).queryKey,
        (messages) => [...(messages ?? []), message],
      );
      setText('');
      requestAnimationFrame(() =>
        list.current?.lastElementChild?.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        }),
      );
    },
  });

  const submit = () => {
    if (text.trim() && !send.isPending) send.mutate(text.trim());
  };

  return (
    <DetailCard title="Üzenetek">
      {isPending && (
        <div className="space-y-4">
          <Skeleton className="h-14 w-2/3 rounded-2xl" />
          <Skeleton className="ml-auto h-10 w-1/2 rounded-2xl" />
        </div>
      )}
      {isError && (
        <p className="text-sm text-muted-foreground">
          Nem sikerült betölteni az üzeneteket. Próbáld újra később!
        </p>
      )}
      {data?.length === 0 && (
        <div className="flex flex-col items-center py-6 text-center">
          <span className="grid size-12 place-items-center rounded-full bg-primary/10 text-primary">
            <MessagesSquareIcon className="size-5" />
          </span>
          <p className="mt-4 font-medium">
            Üzenetet írhatsz nekünk a felkérésedhez
          </p>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Kérdésed van, vagy változott valami? Írd meg itt, és válaszolunk.
          </p>
        </div>
      )}
      {!!data?.length && (
        <ol aria-label="Üzenetek" className="space-y-5" ref={list}>
          {data.map((message) => (
            <Message
              key={message.id}
              message={message}
              own={message.author.id === user?.id}
              requestId={requestId}
            />
          ))}
        </ol>
      )}
      <form
        className="mt-6 border-t pt-6"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <label className="sr-only" htmlFor="new-message">
          Új üzenet
        </label>
        <div className="flex items-end gap-3">
          <Textarea
            className="max-h-48 min-h-11 resize-none"
            id="new-message"
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                submit();
              }
            }}
            placeholder="Írj nekünk…"
            // Disabling it would drop the focus while the message is sent.
            readOnly={send.isPending}
            rows={1}
            value={text}
          />
          <Button
            aria-label="Küldés"
            disabled={send.isPending || !text.trim()}
            size="icon-lg"
            type="submit"
          >
            {send.isPending ? (
              <Loader2Icon className="animate-spin" />
            ) : (
              <SendIcon />
            )}
          </Button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Ha válaszolunk, e-mailben is értesítünk.
        </p>
      </form>
    </DetailCard>
  );
}
