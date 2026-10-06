import { useMutation } from '@tanstack/react-query';
import { cn } from 'cn';
import { CheckIcon, Loader2Icon } from 'lucide-react';
import { toast } from 'sonner';

import { getApiErrorMessage } from 'api/errors';
import { meApi } from 'api/http';
import type { AvatarProviderEnum as AvatarProvider, User } from 'api/models';
import { avatarProviderLabels } from 'helpers/avatar';
import { cacheUser } from 'helpers/session';

export default function AvatarPicker({ user }: { user: User }) {
  // { provider: <selected>, <provider>: <url or null>, ... }
  const avatars = Object.entries(
    user.profile.avatar as Record<string, string | null>,
  ).filter(
    (entry): entry is [AvatarProvider, string] =>
      entry[0] in avatarProviderLabels && !!entry[1],
  );

  const select = useMutation({
    mutationFn: async (provider: AvatarProvider) =>
      (await meApi.mePartialUpdate({ profile: { avatar_provider: provider } }))
        .data,
    onError: (error) =>
      toast.error('Nem sikerült beállítani a profilképet.', {
        description: getApiErrorMessage(error),
      }),
    onSuccess: cacheUser,
  });

  if (!avatars.length) {
    return (
      <p className="text-sm leading-relaxed text-muted-foreground">
        Még nincs profilképed. Tölts fel egyet a{' '}
        <a
          className="text-foreground underline underline-offset-4"
          href="https://gravatar.com"
          rel="noreferrer"
          target="_blank"
        >
          Gravatarra
        </a>
        , vagy kapcsold össze a Google- vagy Microsoft-fiókodat. A Gravatarra
        feltöltött kép a következő bejelentkezés után jelenik meg.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      {avatars.map(([provider, url]) => {
        const selected = url === user.profile.avatar_url;
        const pending = select.isPending && select.variables === provider;

        return (
          <button
            aria-pressed={selected}
            className={cn(
              'group flex flex-col items-center gap-3 rounded-2xl border p-4 text-sm transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-default',
              selected
                ? 'border-primary bg-primary/10'
                : 'hover:border-primary/40 hover:bg-muted/50',
            )}
            disabled={selected || select.isPending}
            key={provider}
            onClick={() => select.mutate(provider)}
            type="button"
          >
            <span className="relative w-full max-w-32">
              <img
                alt=""
                className="aspect-square w-full rounded-full object-cover"
                src={url}
              />
              {(selected || pending) && (
                <span className="absolute right-0 bottom-0 grid size-8 place-items-center rounded-full bg-primary text-primary-foreground ring-4 ring-card">
                  {pending ? (
                    <Loader2Icon className="size-4 animate-spin" />
                  ) : (
                    <CheckIcon className="size-4" />
                  )}
                </span>
              )}
            </span>
            <span className={cn(!selected && 'text-muted-foreground')}>
              {avatarProviderLabels[provider]}
            </span>
          </button>
        );
      })}
    </div>
  );
}
