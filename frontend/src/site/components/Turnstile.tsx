import { type Ref, useImperativeHandle, useRef, useState } from 'react';

import {
  Turnstile as TurnstileWidget,
  type TurnstileInstance,
} from '@marsidev/react-turnstile';
import { cn } from 'cn';

export const CAPTCHA_FAILED =
  'Nem sikerült a biztonsági ellenőrzés. Frissítsd az oldalt, és próbáld újra!';

export type TurnstileHandle = {
  getResponsePromise(): Promise<string>;
  reset(): void;
};

// Most visitors pass unnoticed, the widget only shows up when Cloudflare wants
// a click. Read the token with getResponsePromise(), it waits for the check.
export default function Turnstile({
  className,
  ref,
  show = true,
}: {
  className?: string;
  ref?: Ref<TurnstileHandle>;
  show?: boolean;
}) {
  const widget = useRef<TurnstileInstance>(null);
  const [status, setStatus] = useState<'error' | 'hidden' | 'interactive'>(
    'hidden',
  );

  useImperativeHandle(ref, () => ({
    async getResponsePromise() {
      if (!widget.current) throw new Error('Turnstile has not loaded.');
      return widget.current.getResponsePromise();
    },
    reset() {
      widget.current?.reset();
    },
  }));

  return (
    <div
      className={cn(
        'flex flex-col gap-2',
        // Out of the flow, so it leaves no gap in the form.
        (status === 'hidden' || !show) && 'absolute size-0 overflow-hidden',
        className,
      )}
      inert={!show}
    >
      {show && status === 'interactive' && (
        <p className="text-sm text-muted-foreground">
          Még egy gyors ellenőrzés, és már mehet is.
        </p>
      )}
      {show && status === 'error' && (
        <p className="text-sm text-destructive" role="alert">
          {CAPTCHA_FAILED}
        </p>
      )}
      <TurnstileWidget
        onBeforeInteractive={() => setStatus('interactive')}
        onError={() => setStatus('error')}
        // Only a reset makes getResponsePromise() wait for the new token; after
        // the widget's own refresh it returns the expired one or none.
        onExpire={() => widget.current?.reset()}
        onSuccess={() => setStatus('hidden')}
        onUnsupported={() => setStatus('error')}
        options={{
          appearance: 'interaction-only',
          language: 'hu',
          refreshExpired: 'manual',
          theme: 'dark',
        }}
        ref={widget}
        siteKey={import.meta.env.VITE_TURNSTILE_SITE_KEY}
      />
    </div>
  );
}
