import {
  type ComponentProps,
  type ComponentType,
  useEffect,
  useRef,
  useState,
} from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { cn } from 'cn';
import { Link2Icon, Loader2Icon, Unlink2Icon } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router';
import { toast } from 'sonner';

import { getApiErrorMessage } from 'api/errors';
import { meApi } from 'api/http';
import type { User } from 'api/models';
import { meQuery } from 'helpers/session';
import {
  AuthSchIcon,
  GoogleIcon,
  MicrosoftIcon,
} from 'site/components/BrandIcons';
import { Button } from 'site/components/ui/button';
import { getAuthorizationUrl, type OAuthProvider } from 'site/lib/oauth';

type LoginMethod = {
  // The account in accusative with its article, for the toasts.
  account: string;
  icon: ComponentType<ComponentProps<'svg'>>;
  iconClassName?: string;
  label: string;
  provider: OAuthProvider;
};

const loginMethods: LoginMethod[] = [
  {
    account: 'az AuthSCH-fiókodat',
    icon: AuthSchIcon,
    iconClassName: 'text-[#0a3a66]',
    label: 'AuthSCH',
    provider: 'authsch',
  },
  {
    account: 'a Google-fiókodat',
    icon: GoogleIcon,
    label: 'Google',
    provider: 'google-oauth2',
  },
  {
    account: 'a Microsoft-fiókodat',
    icon: MicrosoftIcon,
    label: 'Microsoft',
    provider: 'microsoft-graph',
  },
];

function accountOf(provider: OAuthProvider) {
  return (
    loginMethods.find((method) => method.provider === provider)?.account ??
    'a fiókodat'
  );
}

type ConnectState = { code?: string; nonce?: string; provider?: OAuthProvider };

export default function LoginMethods({ user }: { user: User }) {
  const queryClient = useQueryClient();
  const location = useLocation();
  const navigate = useNavigate();
  const { code, nonce, provider } = (location.state ?? {}) as ConnectState;
  const [redirecting, setRedirecting] = useState<OAuthProvider | null>(null);
  const attempted = useRef(false);

  const connected = new Set(
    user.social_accounts.map((account) => account.provider),
  );
  // The BSS login of staff counts too, it is just not shown here.
  const lastMethod = user.social_accounts.length <= 1;

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: meQuery().queryKey });

  const connect = useMutation({
    mutationFn: (values: {
      code: string;
      nonce?: string;
      provider: OAuthProvider;
    }) =>
      meApi.meSocialCreate(values.provider, {
        code: values.code,
        nonce: values.nonce,
      }),
    onError: (error) =>
      toast.error('Nem sikerült összekapcsolni a fiókot.', {
        description: getApiErrorMessage(error),
      }),
    onSettled: () =>
      void navigate(location.pathname, { replace: true, state: null }),
    onSuccess: async (_, values) => {
      await refresh();
      toast.success(`Összekapcsoltuk ${accountOf(values.provider)}.`);
    },
  });

  const disconnect = useMutation({
    mutationFn: (target: OAuthProvider) => meApi.meSocialDestroy(target),
    onError: (error) =>
      toast.error('Nem sikerült leválasztani a fiókot.', {
        description: getApiErrorMessage(error),
      }),
    onSuccess: async (_, target) => {
      await refresh();
      toast.success(`Leválasztottuk ${accountOf(target)}.`);
    },
  });

  // The provider sends the user back here through /redirect with a code.
  const { mutate: connectAccount } = connect;
  useEffect(() => {
    if (code && provider && !attempted.current) {
      attempted.current = true;
      connectAccount({ code, nonce, provider });
    }
  }, [code, connectAccount, nonce, provider]);

  // Going back from the provider restores the page with a spinning button.
  useEffect(() => {
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) setRedirecting(null);
    };
    window.addEventListener('pageshow', handlePageShow);
    return () => window.removeEventListener('pageshow', handlePageShow);
  }, []);

  const busy = !!redirecting || connect.isPending || disconnect.isPending;

  return (
    <>
      <p className="text-sm leading-relaxed text-muted-foreground">
        Ezekkel a fiókokkal tudsz bejelentkezni. A Google- és a
        Microsoft-fiókodról a profilképedet is áthozzuk.
      </p>
      <ul className="mt-5 divide-y">
        {loginMethods.map(
          ({ icon: Icon, iconClassName, label, provider: method }) => {
            const isConnected = connected.has(method);
            const working =
              redirecting === method ||
              (connect.isPending && connect.variables.provider === method) ||
              (disconnect.isPending && disconnect.variables === method);

            return (
              <li
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
                key={method}
              >
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-white">
                  <Icon className={cn('size-5', iconClassName)} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{label}</p>
                  <p
                    className={cn(
                      'flex items-center gap-1.5 text-sm',
                      isConnected ? 'text-success' : 'text-muted-foreground',
                    )}
                  >
                    {isConnected && (
                      <span className="size-1.5 rounded-full bg-current" />
                    )}
                    {isConnected ? 'Összekapcsolva' : 'Nincs összekapcsolva'}
                  </p>
                </div>
                {isConnected ? (
                  <Button
                    className="max-sm:w-8 max-sm:px-0"
                    disabled={busy || lastMethod}
                    onClick={() => disconnect.mutate(method)}
                    size="sm"
                    variant="outline"
                  >
                    {working ? (
                      <Loader2Icon className="animate-spin" />
                    ) : (
                      <Unlink2Icon />
                    )}
                    <span className="max-sm:sr-only">Leválasztás</span>
                  </Button>
                ) : (
                  <Button
                    className="max-sm:w-8 max-sm:px-0"
                    disabled={busy}
                    onClick={() => {
                      setRedirecting(method);
                      window.location.assign(
                        getAuthorizationUrl(method, 'profile'),
                      );
                    }}
                    size="sm"
                    variant="outline"
                  >
                    {working ? (
                      <Loader2Icon className="animate-spin" />
                    ) : (
                      <Link2Icon />
                    )}
                    <span className="max-sm:sr-only">Összekapcsolás</span>
                  </Button>
                )}
              </li>
            );
          },
        )}
      </ul>
      {lastMethod && connected.size > 0 && !connected.has('bss-login') && (
        <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
          Az egyetlen bejelentkezési módodat nem választhatod le, különben nem
          tudnál belépni.
        </p>
      )}
    </>
  );
}
