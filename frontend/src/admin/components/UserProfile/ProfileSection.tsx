import { lazy, useEffect, useState } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Avatar } from 'primereact/avatar';
import { Button } from 'primereact/button';
import { Chip } from 'primereact/chip';
import { Divider } from 'primereact/divider';
import { InputText } from 'primereact/inputtext';
import { Message } from 'primereact/message';
import { SplitButton } from 'primereact/splitbutton';
import { Tag } from 'primereact/tag';
import { classNames } from 'primereact/utils';
import { useForm } from 'react-hook-form';
import type { SubmitHandler } from 'react-hook-form';

import { userUpdateMutation } from 'admin/api/mutations';
import { queryKeys } from 'admin/api/queryKeys';
import FormField from 'admin/components/FormField/FormField';
import { showErrorToast } from 'admin/helpers/showErrorToast';
import { useToast } from 'admin/providers/ToastProvider';
import { AvatarProviderEnum, UserAdminRetrieveUpdate } from 'api';
import { isNotFound, setFieldErrors } from 'api/errors';
import { getAvatarStyle, getInitials } from 'helpers/avatar';
import { getUserId, isAdmin } from 'helpers/LocalStorageHelper';
import { formatName } from 'helpers/names';
import { formatPhone, toE164 } from 'helpers/phone';

const AvatarDialog = lazy(
  () => import('admin/components/UserProfile/AvatarDialog'),
);

interface ProfileSectionProps {
  userData: UserAdminRetrieveUpdate;
}

const socialAccounts: Record<string, { icon: string; label: string }> = {
  authsch: {
    icon: 'pi icon-sch',
    label: 'AuthSCH',
  },
  'bss-login': {
    icon: 'pi pi-shield',
    label: 'BSS Login',
  },
  'google-oauth2': {
    icon: 'pi pi-google',
    label: 'Google',
  },
  'microsoft-graph': {
    icon: 'pi pi-microsoft',
    label: 'Microsoft',
  },
};

function toFormValues(user: UserAdminRetrieveUpdate) {
  const phone = user.phone_number;
  return {
    ...user,
    phone_number: phone && formatPhone(phone),
  };
}

function getUserRole(role: string, banned: boolean) {
  if (banned) return 'Kitiltva';
  switch (role) {
    case 'admin':
      return 'Adminisztrátor';
    case 'staff':
      return 'BSS Tag';
    default:
      return 'Felhasználó';
  }
}

const ProfileSection = ({ userData }: ProfileSectionProps) => {
  const [avatarDialogVisible, setAvatarDialogVisible] =
    useState<boolean>(false);
  const { control, handleSubmit, reset, setError } =
    useForm<UserAdminRetrieveUpdate>({
      defaultValues: toFormValues(userData),
    });
  const { isPending, mutateAsync } = useMutation(
    userUpdateMutation(userData.id),
  );
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const userIsStaff = ['admin', 'staff'].includes(userData.role);
  const disabled = isPending || userIsStaff || !isAdmin();
  const fullName =
    formatName(userData.last_name, userData.first_name) || userData.username;

  const saveButtonItems = [
    {
      command: () => {
        reset();
      },
      icon: 'pi pi-refresh',
      label: 'Visszaállítás',
    },
  ];

  useEffect(() => {
    reset(toFormValues(userData));
  }, [reset, userData]);

  const onAvatarSave = async (provider: string) => {
    await mutateAsync({ avatar_provider: provider as AvatarProviderEnum })
      .then(async (response) => {
        showToast({
          detail: 'Profilkép módosítva',
          life: 3000,
          severity: 'success',
          summary: 'Siker',
        });

        await queryClient.invalidateQueries({
          queryKey: queryKeys.user(response.data.id),
        });

        setAvatarDialogVisible(false);
      })
      .catch(async (error) => {
        showErrorToast(error);
      });
  };

  const onSubmit: SubmitHandler<UserAdminRetrieveUpdate> = async (data) => {
    const phone = data.phone_number;
    await mutateAsync({ ...data, phone_number: phone && toE164(phone) })
      .then(async (response) => {
        showToast({
          detail: 'Felhasználó módosítva',
          life: 3000,
          severity: 'success',
          summary: 'Siker',
        });

        await queryClient.invalidateQueries({
          queryKey: queryKeys.user(response.data.id),
        });
      })
      .catch(async (error) => {
        if (setFieldErrors(error, setError)) return;
        if (isNotFound(error)) {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.user(userData.id),
          });
        }
        showErrorToast(error);
      });
  };

  return (
    <>
      <AvatarDialog
        loading={isPending}
        onHide={() => {
          setAvatarDialogVisible(false);
        }}
        onSave={onAvatarSave}
        userData={userData}
        visible={avatarDialogVisible}
      />
      <div className="font-semibold mt-3 text-900 text-lg">Profil</div>
      <Divider />
      <form className="flex flex-column-reverse gap-5 md:flex-row">
        <div className="flex-auto formgrid grid p-fluid">
          <FormField
            className="col-12 mb-4 lg:col-6"
            control={control}
            disabled={disabled}
            label="Vezetéknév"
            name="last_name"
          >
            <InputText type="text" />
          </FormField>
          <FormField
            className="col-12 mb-4 lg:col-6"
            control={control}
            disabled={disabled}
            label="Keresztnév"
            name="first_name"
          >
            <InputText type="text" />
          </FormField>
          <FormField
            className="col-12 mb-4"
            control={control}
            disabled={disabled}
            icon="pi-envelope"
            label="E-mail cím"
            name="email"
          >
            <InputText type="email" />
          </FormField>
          <FormField
            className="col-12 mb-4"
            control={control}
            disabled={disabled}
            icon="pi-phone"
            label="Telefonszám"
            name="phone_number"
          >
            <InputText type="tel" />
          </FormField>
          <div
            className={classNames(
              'col-12 field',
              userData.groups.length > 0 || userData.social_accounts.length > 0
                ? 'mb-4'
                : 'mb-0',
            )}
          >
            <label className="font-medium text-900">Jogosultság</label>
            <div className="card flex flex-wrap gap-2">
              <Tag severity={userData.ban ? 'danger' : null}>
                {getUserRole(userData.role, !!userData.ban)}
              </Tag>
            </div>
          </div>
          {userData.groups.length > 0 && (
            <div
              className={classNames(
                'col-12 field',
                userData.social_accounts.length > 0
                  ? 'lg:col-6 lg:mb-0 mb-4'
                  : 'mb-0',
              )}
            >
              <label className="font-medium text-900">Csoportok</label>
              <div className="card flex flex-wrap gap-2">
                {userData.groups
                  .sort((a, b) => a.localeCompare(b))
                  .map((group, index) => {
                    return <Chip key={index} label={group} />;
                  })}
              </div>
            </div>
          )}
          {userData.social_accounts.length > 0 && (
            <div
              className={classNames(
                'col-12 field mb-0',
                userData.groups.length > 0 && 'lg:col-6',
              )}
            >
              <label className="font-medium text-900">
                Összekapcsolt profilok
              </label>
              <div className="card flex flex-wrap gap-2">
                {userData.social_accounts
                  .sort((a, b) => a.provider.localeCompare(b.provider))
                  .map((account) => {
                    const provider = account.provider;
                    return (
                      <Chip
                        icon={socialAccounts[provider].icon}
                        key={provider}
                        label={socialAccounts[provider].label}
                      />
                    );
                  })}
              </div>
            </div>
          )}
          <Divider />
          <div className="col-12 flex flex-wrap-reverse gap-2">
            <SplitButton
              className="w-auto"
              disabled={disabled}
              icon="pi pi-save"
              label="Mentés"
              loading={isPending}
              model={saveButtonItems}
              onClick={handleSubmit(onSubmit)}
            />
            {userIsStaff && (
              <Message
                severity="warn"
                text="Az adatokat a BSS címtár szolgáltatásában kell módosítani."
              />
            )}
          </div>
        </div>
        <div className="align-items-center flex flex-column flex-order-1">
          <span className="font-medium mb-2 text-900">Profilkép</span>
          <Avatar
            className="h-10rem w-10rem"
            image={userData.avatar_url || undefined}
            label={getInitials(fullName)}
            pt={{ label: { className: 'font-medium select-none' } }}
            shape="circle"
            style={{ ...getAvatarStyle(fullName), fontSize: '4.375rem' }}
          />
          <Button
            className="-mt-4 p-button-rounded"
            disabled={isPending || (!isAdmin() && userData.id !== getUserId())}
            icon="pi pi-pencil"
            onClick={() => {
              setAvatarDialogVisible(true);
            }}
            type="button"
          />
        </div>
      </form>
    </>
  );
};

export default ProfileSection;
