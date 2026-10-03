import type { Ref } from 'react';

import {
  Turnstile as TurnstileWidget,
  type TurnstileInstance,
} from '@marsidev/react-turnstile';

import { useDarkMode } from 'site/hooks/useDarkMode';

type TurnstileProps = {
  onTokenChange: (token: string | null) => void;
  ref?: Ref<TurnstileInstance>;
};

export default function Turnstile({ onTokenChange, ref }: TurnstileProps) {
  const [darkMode] = useDarkMode();

  return (
    <TurnstileWidget
      // The widget only reads its theme when it is created.
      key={darkMode ? 'dark' : 'light'}
      onError={() => onTokenChange(null)}
      onExpire={() => onTokenChange(null)}
      onSuccess={onTokenChange}
      options={{
        language: 'hu',
        size: 'flexible',
        theme: darkMode ? 'dark' : 'light',
      }}
      ref={ref}
      siteKey={import.meta.env.VITE_TURNSTILE_SITE_KEY}
    />
  );
}
