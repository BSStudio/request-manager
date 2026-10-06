import { useState } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { hu } from 'date-fns/locale';
import {
  EllipsisIcon,
  Loader2Icon,
  PencilIcon,
  Trash2Icon,
} from 'lucide-react';
import { toast } from 'sonner';

import { getApiErrorMessage } from 'api/errors';
import { requestsApi } from 'api/http';
import type { CommentListRetrieve } from 'api/models';
import { getInitials } from 'helpers/names';
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
import { Avatar, AvatarFallback, AvatarImage } from 'site/components/ui/avatar';
import { Button } from 'site/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from 'site/components/ui/dropdown-menu';
import { Textarea } from 'site/components/ui/textarea';
import { formatMessageTime } from 'site/lib/dates';
import { requestCommentsQuery } from 'site/lib/queries';

function MessageTime({ created }: { created: string }) {
  const date = new Date(created);
  return (
    <time
      dateTime={created}
      title={format(date, 'yyyy. MMMM d., EEEE HH:mm', { locale: hu })}
    >
      {formatMessageTime(date)}
    </time>
  );
}

function StudioMessage({ message }: { message: CommentListRetrieve }) {
  return (
    <li className="flex gap-3">
      <Avatar className="mt-0.5">
        <AvatarImage alt="" src={message.author.avatar_url || undefined} />
        <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
          {getInitials(message.author.full_name)}
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0 max-w-[85%]">
        <p className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">
            {message.author.full_name}
          </span>
          <span className="rounded bg-primary/15 px-1.5 py-px text-[0.625rem] font-semibold tracking-wider text-primary">
            BSS
          </span>
          <MessageTime created={message.created} />
        </p>
        <p className="mt-1 rounded-2xl rounded-tl-md bg-muted px-4 py-2.5 text-sm leading-relaxed break-words whitespace-pre-wrap">
          {message.text}
        </p>
      </div>
    </li>
  );
}

type OwnMessageProps = {
  message: CommentListRetrieve;
  requestId: number;
};

function OwnMessage({ message, requestId }: OwnMessageProps) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const { queryKey } = requestCommentsQuery(requestId);

  const save = useMutation({
    mutationFn: async (text: string) =>
      (
        await requestsApi.requestsCommentsPartialUpdate(message.id, requestId, {
          text,
        })
      ).data,
    onError: (error) =>
      toast.error('Nem sikerült menteni az üzenetet.', {
        description: getApiErrorMessage(error),
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKey, (messages) =>
        messages?.map((item) => (item.id === data.id ? data : item)),
      );
      setDraft(null);
    },
  });

  const remove = useMutation({
    mutationFn: () =>
      requestsApi.requestsCommentsDestroy(message.id, requestId),
    onError: (error) =>
      toast.error('Nem sikerült törölni az üzenetet.', {
        description: getApiErrorMessage(error),
      }),
    onSuccess: () => {
      queryClient.setQueryData(queryKey, (messages) =>
        messages?.filter((item) => item.id !== message.id),
      );
      setConfirmingDelete(false);
    },
  });

  if (draft !== null) {
    return (
      <li>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate(draft.trim());
          }}
        >
          <label className="sr-only" htmlFor={`message-${message.id}`}>
            Üzenet szerkesztése
          </label>
          <Textarea
            autoFocus
            className="max-h-64"
            id={`message-${message.id}`}
            onChange={(event) => setDraft(event.target.value)}
            value={draft}
          />
          <div className="mt-2 flex justify-end gap-2">
            <Button
              disabled={save.isPending}
              onClick={() => setDraft(null)}
              size="sm"
              type="button"
              variant="ghost"
            >
              Mégsem
            </Button>
            <Button
              disabled={save.isPending || !draft.trim()}
              size="sm"
              type="submit"
            >
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
      </li>
    );
  }

  return (
    <li className="flex flex-col items-end">
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        <MessageTime created={message.created} />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              aria-label="Műveletek"
              className="relative -my-1 text-muted-foreground pointer-coarse:after:absolute pointer-coarse:after:-inset-2.5"
              size="icon-xs"
              variant="ghost"
            >
              <EllipsisIcon />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={() => setDraft(message.text)}>
              <PencilIcon />
              Szerkesztés
            </DropdownMenuItem>
            <DropdownMenuItem
              onSelect={() => setConfirmingDelete(true)}
              variant="destructive"
            >
              <Trash2Icon />
              Törlés
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <p className="mt-1 max-w-[85%] rounded-2xl rounded-tr-md bg-primary/15 px-4 py-2.5 text-sm leading-relaxed break-words whitespace-pre-wrap">
        {message.text}
      </p>
      <AlertDialog onOpenChange={setConfirmingDelete} open={confirmingDelete}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Törlöd az üzenetet?</AlertDialogTitle>
            <AlertDialogDescription>
              Az üzenet végleg eltűnik a beszélgetésből.
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
    </li>
  );
}

type MessageProps = {
  message: CommentListRetrieve;
  own: boolean;
  requestId: number;
};

export default function Message({ message, own, requestId }: MessageProps) {
  return own ? (
    <OwnMessage message={message} requestId={requestId} />
  ) : (
    <StudioMessage message={message} />
  );
}
