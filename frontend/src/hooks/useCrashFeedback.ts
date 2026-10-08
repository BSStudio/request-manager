import { useState } from 'react';

import { sendFeedback } from '@sentry/react';
import { useMutation } from '@tanstack/react-query';

export const crashFeedbackText = {
  error: 'Nem sikerült elküldeni. Próbáld újra!',
  hint: 'Ha leírod, könnyebben megtaláljuk és kijavítjuk.',
  label: 'Mit csináltál, amikor a hiba történt?',
  send: 'Küldés',
  thanks: 'Köszönjük, hogy segítesz kijavítani a hibát!',
};

export function useCrashFeedback(eventId: string) {
  const [message, setMessage] = useState('');
  const feedback = useMutation({
    mutationFn: (text: string) =>
      sendFeedback({ associatedEventId: eventId, message: text }),
    // Offline, Sentry fails at once and the form says so, instead of waiting.
    networkMode: 'always',
  });

  const submit = () => {
    if (message.trim()) feedback.mutate(message.trim());
  };

  return { feedback, message, setMessage, submit };
}
