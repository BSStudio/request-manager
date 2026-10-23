import { useState } from 'react';

import { useQuery, useQueryClient } from '@tanstack/react-query';

import {
  disablePush,
  enablePush,
  pushErrors,
  pushKeyQuery,
  pushStateQuery,
} from 'helpers/push';

// The notifications pages point to the profile while push could be turned on.
export function usePushOffered() {
  const { data: publicKey } = useQuery(pushKeyQuery());
  const { data: state } = useQuery(pushStateQuery());
  return !!publicKey && state === 'off';
}

export function usePushSubscription(
  onError: (message: string, error: unknown) => void,
) {
  const queryClient = useQueryClient();
  const { data: publicKey } = useQuery(pushKeyQuery());
  const { data: state } = useQuery(pushStateQuery());
  const [pending, setPending] = useState(false);
  const stateKey = pushStateQuery().queryKey;

  // Not a mutation: that calls enablePush only after an await, too late for
  // the permission prompt.
  const toggle = () => {
    if (!publicKey) return;
    const enabling = state !== 'on';
    setPending(true);
    (enabling
      ? enablePush(publicKey)
      : disablePush().then(() => 'off' as const)
    )
      .then((next) => queryClient.setQueryData(stateKey, next))
      .catch((error: unknown) => {
        onError(enabling ? pushErrors.enable : pushErrors.disable, error);
        void queryClient.invalidateQueries({ queryKey: stateKey });
      })
      .finally(() => setPending(false));
  };

  return { available: !!publicKey, pending, state, toggle };
}
