import { forwardRef, useState } from 'react';

import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import type { DialogProps } from 'primereact/dialog';
import { RadioButton } from 'primereact/radiobutton';
import { classNames } from 'primereact/utils';

import type { AvatarProviderEnum } from 'api/models';
import { UserAdminRetrieveUpdate } from 'api/models/user-admin-retrieve-update';
import { avatarProviderLabels } from 'helpers/avatar';

interface AvatarDialogProps extends DialogProps {
  loading: boolean;
  onSave(provider: string): void;
  userData: UserAdminRetrieveUpdate;
}

type AvatarOptionProps = {
  image: string | null;
  onClick: React.MouseEventHandler<HTMLDivElement>;
  provider: AvatarProviderEnum;
  selected: boolean;
};

const AvatarOption = ({
  image,
  onClick,
  provider,
  selected,
}: AvatarOptionProps) => {
  return (
    <div className="col-12 lg:col-4">
      <div
        className={classNames(
          'border-2 border-round h-full shadow-1 surface-ground',
          {
            'border-blue-500 shadow-3': selected,
            'border-transparent': !selected,
            'cursor-pointer': !!image,
          },
        )}
        onClick={image ? onClick : undefined}
      >
        {image ? (
          <img
            alt={avatarProviderLabels[provider]}
            className="block w-full"
            src={image}
          />
        ) : (
          <div
            className="align-items-center flex justify-content-center surface-200 text-500 text-xl"
            style={{ aspectRatio: '1' }}
          >
            Nem elérhető
          </div>
        )}
        <div className="align-items-center flex flex-column gap-3 p-3">
          <div
            className={classNames('font-medium text-xl', {
              'text-400': !image,
              'text-900': !!image,
            })}
          >
            {avatarProviderLabels[provider]}
          </div>
          <RadioButton
            checked={selected}
            disabled={!image}
            name={provider}
            value={provider}
          />
        </div>
      </div>
    </div>
  );
};

const AvatarDialog = forwardRef<React.Ref<HTMLDivElement>, AvatarDialogProps>(
  ({ loading, onHide, onSave, userData, visible, ...props }, ref) => {
    const [selectedProvider, setSelectedProvider] = useState<string>(
      userData.avatar['provider'],
    );
    const [wasVisible, setWasVisible] = useState(visible);

    // Each opening starts from the saved avatar, not the last unsaved pick.
    if (visible !== wasVisible) {
      setWasVisible(visible);
      if (visible) setSelectedProvider(userData.avatar['provider']);
    }

    const renderFooter = () => {
      return (
        <div>
          <Button
            className="p-button-text"
            disabled={loading}
            icon="pi pi-times"
            label="Mégsem"
            onClick={onHide}
          />
          <Button
            autoFocus
            disabled={!selectedProvider}
            icon="pi pi-check"
            label="Mentés"
            loading={loading}
            onClick={() => {
              onSave(selectedProvider);
            }}
          />
        </div>
      );
    };

    return (
      <Dialog
        breakpoints={{ '768px': '95vw' }}
        footer={renderFooter}
        header="Profilkép"
        onHide={onHide}
        style={{ width: '50vw' }}
        visible={visible}
        {...props}
        {...ref}
      >
        <div className="grid">
          {(Object.keys(avatarProviderLabels) as AvatarProviderEnum[]).map(
            (provider) => (
              <AvatarOption
                key={provider}
                image={userData.avatar[provider]}
                onClick={() => {
                  setSelectedProvider(provider);
                }}
                provider={provider}
                selected={selectedProvider === provider}
              />
            ),
          )}
        </div>
      </Dialog>
    );
  },
);

AvatarDialog.displayName = 'AvatarDialog';
export default AvatarDialog;
