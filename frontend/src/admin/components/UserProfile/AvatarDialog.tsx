import { forwardRef, useEffect, useState } from 'react';

import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import type { DialogProps } from 'primereact/dialog';
import { RadioButton } from 'primereact/radiobutton';
import { classNames } from 'primereact/utils';

import { UserAdminRetrieveUpdate } from 'api/models/user-admin-retrieve-update';

interface AvatarDialogProps extends DialogProps {
  loading: boolean;
  onSave(provider: string): void;
  userData: UserAdminRetrieveUpdate;
}

type AvatarOptionProps = {
  image: string | null;
  onClick: React.MouseEventHandler<HTMLDivElement>;
  provider: string;
  selected: boolean;
};

const avatarProvider: Record<string, string> = {
  'google-oauth2': 'Google',
  gravatar: 'Gravatar',
  'microsoft-graph': 'Microsoft',
};

const AvatarOption = ({
  image,
  onClick,
  provider,
  selected,
}: AvatarOptionProps) => {
  const fallbackImage =
    'https://placehold.co/500x500?text=Nem+el%C3%A9rhet%C5%91';

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
        <img
          alt={avatarProvider[provider]}
          className="w-full"
          src={image || fallbackImage}
        />
        <div className="align-items-center flex flex-column gap-3 p-3">
          <div
            className={classNames('font-medium text-xl', {
              'text-400': !image,
              'text-900': !!image,
            })}
          >
            {avatarProvider[provider]}
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
      userData.profile.avatar['provider'],
    );

    useEffect(() => {
      setSelectedProvider(userData.profile.avatar['provider']);
    }, [userData, visible]);

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
          {['google-oauth2', 'gravatar', 'microsoft-graph'].map((provider) => (
            <AvatarOption
              key={provider}
              image={userData.profile.avatar[provider]}
              onClick={() => {
                setSelectedProvider(provider);
              }}
              provider={provider}
              selected={selectedProvider === provider}
            />
          ))}
        </div>
      </Dialog>
    );
  },
);

AvatarDialog.displayName = 'AvatarDialog';
export default AvatarDialog;
