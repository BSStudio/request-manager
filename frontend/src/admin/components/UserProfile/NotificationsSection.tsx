import { Divider } from 'primereact/divider';
import { InputSwitch } from 'primereact/inputswitch';
import { Message } from 'primereact/message';

import { getErrorMessage } from 'admin/helpers/ErrorMessageProvider';
import { useToast } from 'admin/providers/ToastProvider';
import { pushDescriptions, pushHints } from 'helpers/push';
import { usePushSubscription } from 'hooks/usePushSubscription';

const NotificationsSection = () => {
  const { showToast } = useToast();
  const { pending, state, toggle } = usePushSubscription((message, error) =>
    showToast({
      detail: getErrorMessage(error),
      life: 3000,
      severity: 'error',
      summary: message,
    }),
  );
  const hint = state && pushHints[state];

  return (
    <>
      <div className="font-semibold mt-3 text-900 text-lg">Értesítések</div>
      <Divider />
      <div className="align-items-center flex gap-3 justify-content-between">
        <div>
          <label className="font-medium text-900" htmlFor="push">
            Push értesítések
          </label>
          <p className="line-height-3 m-0 mt-1 text-600">
            {pushDescriptions.admin}
          </p>
        </div>
        <InputSwitch
          checked={state === 'on'}
          className="flex-shrink-0"
          disabled={pending || (state !== 'on' && state !== 'off')}
          inputId="push"
          onChange={toggle}
        />
      </div>
      {hint && (
        <Message
          className="justify-content-start mt-4 w-full"
          severity="info"
          text={hint}
        />
      )}
    </>
  );
};

export default NotificationsSection;
