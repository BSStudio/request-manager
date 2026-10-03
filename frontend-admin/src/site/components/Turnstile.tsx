import { type Ref, useState } from 'react';

import {
  Turnstile as TurnstileWidget,
  type TurnstileInstance,
} from '@marsidev/react-turnstile';
import { cn } from 'cn';

import { useDarkMode } from 'site/hooks/useDarkMode';

export const CAPTCHA_FAILED =
  'Nem sikerült a biztonsági ellenőrzés. Frissítsd az oldalt, és próbáld újra!';

type TurnstileProps = {
  ref?: Ref<TurnstileInstance>;
};

type ChallengeProps = TurnstileProps & {
  theme: 'dark' | 'light';
};

function Challenge({ ref, theme }: ChallengeProps) {
  const [status, setStatus] = useState<'error' | 'hidden' | 'interactive'>(
    'hidden',
  );

  return (
    <div
      className={cn(
        'flex flex-col gap-2',
        // Out of the flow, so it leaves no gap in the form.
        status === 'hidden' && 'absolute size-0 overflow-hidden',
      )}
    >
      {status === 'interactive' && (
        <p className="text-sm text-muted-foreground">
          Még egy gyors ellenőrzés, és már mehet is.
        </p>
      )}
      {status === 'error' && (
        <p className="text-sm text-destructive" role="alert">
          {CAPTCHA_FAILED}
        </p>
      )}
      <TurnstileWidget
        onBeforeInteractive={() => setStatus('interactive')}
        onError={() => setStatus('error')}
        // The automatic retry after an error can pass without interaction.
        onSuccess={() =>
          setStatus((current) => (current === 'error' ? 'hidden' : current))
        }
        onUnsupported={() => setStatus('error')}
        options={{ appearance: 'interaction-only', language: 'hu', theme }}
        ref={ref}
        siteKey={import.meta.env.VITE_TURNSTILE_SITE_KEY}
      />
    </div>
  );
}

// Most visitors pass unnoticed, the widget only shows up when Cloudflare wants
// a click. Read the token with getResponsePromise(), it waits for the check.
export default function Turnstile({ ref }: TurnstileProps) {
  const [darkMode] = useDarkMode();
  const theme = darkMode ? 'dark' : 'light';

  // The widget only reads its theme when it is created.
  return <Challenge key={theme} ref={ref} theme={theme} />;
}
