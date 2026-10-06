import {
  type ComponentProps,
  type ComponentType,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';

import { isAxiosError } from 'axios';
import { cn } from 'cn';
import {
  ArrowRightIcon,
  ListChecksIcon,
  Loader2Icon,
  MessagesSquareIcon,
  StarIcon,
  UserRoundCheckIcon,
} from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router';
import { toast } from 'sonner';

import { isAdminPath } from 'helpers/isAdminPath';
import {
  getRole,
  hasSession,
  popRedirectedFrom,
  setRedirectedFrom,
} from 'helpers/LocalStorageHelper';
import { signIn, useSessionUser, whenSessionChecked } from 'helpers/session';
import nightSkyImage from 'site/assets/night-sky.webp';
import {
  AuthSchIcon,
  GoogleIcon,
  MicrosoftIcon,
} from 'site/components/BrandIcons';
import BssLogo from 'site/components/BssLogo';
import { Button } from 'site/components/ui/button';
import { usePageTitle } from 'site/hooks/usePageTitle';
import { getAuthorizationUrl, type OAuthProvider } from 'site/lib/oauth';

type LoginLocationState = {
  code?: string;
  from?: string;
  provider?: OAuthProvider;
};

type ProviderButton = {
  icon: ComponentType<ComponentProps<'svg'>>;
  iconClassName?: string;
  label: string;
  provider: OAuthProvider;
};

const providerButtons: ProviderButton[] = [
  {
    icon: AuthSchIcon,
    iconClassName: 'text-[#0a3a66]',
    label: 'Belépés AuthSCH-val',
    provider: 'authsch',
  },
  {
    icon: GoogleIcon,
    label: 'Belépés Google-fiókkal',
    provider: 'google-oauth2',
  },
  {
    icon: MicrosoftIcon,
    label: 'Belépés Microsoft-fiókkal',
    provider: 'microsoft-graph',
  },
];

const benefits = [
  {
    icon: UserRoundCheckIcon,
    text: 'A felkérésnél nem kell újra megadnod az adataidat.',
  },
  {
    icon: ListChecksIcon,
    text: 'Nyomon követheted a felkéréseid állapotát.',
  },
  {
    icon: MessagesSquareIcon,
    text: 'Üzenetet írhatsz nekünk a felkéréseddel kapcsolatban.',
  },
  {
    icon: StarIcon,
    text: 'Értékelheted az elkészült videókat.',
  },
];

const shootingStars = [
  { delay: '2s', left: '78%', top: '10%' },
  { delay: '9s', left: '52%', top: '4%' },
  { delay: '15s', left: '92%', top: '26%' },
];

// Staff work in the admin, which has its own page for every request.
function getLandingPath(role: string) {
  const path = popRedirectedFrom() ?? '/';
  if (!['admin', 'staff'].includes(role)) return path;
  if (path === '/') return '/admin';
  return path.replace(/^\/my-requests\/(\d+)/, '/admin/requests/$1');
}

function getErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    if (error.response?.status === 429) {
      return 'Túl sok próbálkozás. Várj egy percet, és próbáld újra!';
    }
    if (typeof error.response?.data === 'string' && error.response.data) {
      return error.response.data;
    }
  }
  return 'Próbáld újra, vagy válassz másik fiókot.';
}

function LoginPage() {
  usePageTitle('Bejelentkezés');
  const navigate = useNavigate();
  const location = useLocation();
  const user = useSessionUser();
  const { code, from, provider } = (location.state ?? {}) as LoginLocationState;
  const [pending, setPending] = useState<OAuthProvider | 'session' | null>(
    code ? 'session' : null,
  );
  const attempted = useRef(false);

  const leave = useCallback(
    (role: string) => {
      const path = getLandingPath(role);
      if (isAdminPath(path)) {
        window.location.replace(path);
      } else {
        void navigate(path, { replace: true });
      }
    },
    [navigate],
  );

  // The provider sends the user back without the router state.
  useEffect(() => {
    if (from) setRedirectedFrom(from);
  }, [from]);

  useEffect(() => {
    if (code && provider) {
      if (attempted.current) return;
      attempted.current = true;
      signIn(provider, code)
        .then(({ role }) => {
          toast.success('Sikeresen bejelentkeztél.');
          leave(role);
        })
        .catch((error: unknown) => {
          toast.error('Nem sikerült bejelentkezni.', {
            description: getErrorMessage(error),
          });
          setPending(null);
          void navigate(location.pathname, { replace: true, state: null });
        });
    } else if (user && !attempted.current) {
      let cancelled = false;
      // The cached user may belong to an expired session.
      void whenSessionChecked().then(() => {
        if (cancelled || attempted.current || !hasSession()) return;
        attempted.current = true;
        leave(getRole());
      });
      return () => {
        cancelled = true;
      };
    }
  }, [code, provider, user, leave, navigate, location.pathname]);

  // Going back from the provider restores the page with a spinning button.
  useEffect(() => {
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) setPending(null);
    };
    window.addEventListener('pageshow', handlePageShow);
    return () => window.removeEventListener('pageshow', handlePageShow);
  }, []);

  const startLogin = (target: OAuthProvider) => {
    setPending(target);
    window.location.assign(getAuthorizationUrl(target, 'login'));
  };

  return (
    <section className="relative isolate flex min-h-svh flex-1 items-center overflow-hidden bg-ink text-white">
      <img
        alt=""
        className="absolute inset-0 -z-30 size-full object-cover motion-safe:animate-ken-burns"
        src={nightSkyImage}
      />
      <div className="absolute inset-0 -z-20 bg-[linear-gradient(to_top,var(--ink)_5%,transparent_60%),linear-gradient(to_right,color-mix(in_oklab,var(--ink)_70%,transparent),transparent_70%)]" />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 overflow-hidden"
      >
        {shootingStars.map(({ delay, left, top }) => (
          <span
            className="absolute h-px w-32 bg-linear-to-r from-white via-white/50 to-transparent opacity-0 motion-safe:animate-shooting-star"
            key={delay}
            style={{ animationDelay: delay, left, top }}
          />
        ))}
      </div>
      <div className="mx-auto grid w-full max-w-6xl items-center gap-12 px-4 pt-28 pb-16 sm:px-6 lg:grid-cols-[1fr_26rem] lg:gap-20">
        <div className="hidden lg:block">
          <p className="flex items-center gap-3 font-mono text-xs tracking-[0.2em] text-white/70 uppercase">
            <span className="h-px w-8 bg-white/40" />
            Felkéréskezelő
          </p>
          <h2 className="mt-5 max-w-xl text-5xl leading-[1.02] font-bold xl:text-6xl">
            Minden felkérésed egy helyen.
          </h2>
          <ul className="mt-10 space-y-4">
            {benefits.map(({ icon: Icon, text }) => (
              <li className="flex items-start gap-3 text-white/80" key={text}>
                <span className="grid size-9 shrink-0 place-items-center rounded-full bg-white/10 ring-1 ring-white/15">
                  <Icon className="size-4.5" />
                </span>
                <span className="pt-1.5">{text}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="animate-in rounded-3xl bg-ink/60 p-6 shadow-2xl ring-1 ring-white/12 backdrop-blur-2xl duration-700 fade-in slide-in-from-bottom-6 sm:p-8">
          <h1 className="text-3xl font-bold">Bejelentkezés</h1>
          <p className="mt-2 text-white/65">
            Válaszd ki, melyik fiókoddal szeretnél belépni.
          </p>
          {pending === 'session' ? (
            <div
              aria-live="polite"
              className="flex flex-col items-center gap-4 py-12 text-center"
            >
              <Loader2Icon className="size-8 animate-spin text-white/80" />
              <div>
                <p className="font-medium">Bejelentkezés folyamatban…</p>
                <p className="mt-1 text-sm text-white/60">
                  Egy pillanat, ellenőrizzük a fiókodat.
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="mt-8 space-y-3">
                {providerButtons.map(
                  ({ icon: Icon, iconClassName, label, provider: target }) => (
                    <Button
                      className="h-12 w-full justify-start gap-3 rounded-xl bg-white px-4 text-[0.9375rem] text-ink hover:bg-white/85"
                      disabled={pending !== null}
                      key={target}
                      onClick={() => startLogin(target)}
                    >
                      {pending === target ? (
                        <Loader2Icon className="size-5 animate-spin" />
                      ) : (
                        <Icon className={cn('size-5', iconClassName)} />
                      )}
                      {label}
                    </Button>
                  ),
                )}
              </div>
              <div className="my-6 flex items-center gap-3 font-mono text-[0.6875rem] tracking-[0.2em] text-white/45 uppercase">
                <span className="h-px flex-1 bg-white/15" />
                BSS-tagoknak
                <span className="h-px flex-1 bg-white/15" />
              </div>
              <Button
                className="h-12 w-full gap-3 rounded-xl border-white/20 bg-white/5 text-[0.9375rem] text-white hover:bg-white/12 hover:text-white dark:border-white/20 dark:bg-white/5 dark:hover:bg-white/12"
                disabled={pending !== null}
                onClick={() => startLogin('bss-login')}
                variant="outline"
              >
                {pending === 'bss-login' ? (
                  <Loader2Icon className="size-5 animate-spin" />
                ) : (
                  <BssLogo className="size-auto h-5" mono />
                )}
                Belépés BSS-fiókkal
              </Button>
            </>
          )}
          <p className="mt-8 border-t border-white/10 pt-6 text-sm text-white/55">
            Bejelentkezés nélkül is beküldhetsz felkérést.{' '}
            <Link
              className="group inline-flex items-center gap-1 font-medium text-white hover:underline"
              to="/new-request"
            >
              Felkérés beküldése
              <ArrowRightIcon className="size-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
}

export { LoginPage as Component };
