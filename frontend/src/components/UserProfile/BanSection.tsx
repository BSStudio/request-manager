import { useState } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from 'primereact/button';
import { Divider } from 'primereact/divider';
import { InputTextarea } from 'primereact/inputtextarea';

import { BanUser } from 'api/models/ban-user';
import { userBanCreateMutation, userBanDeleteMutation } from 'api/mutations';
import { queryKeys } from 'api/queryKeys';
import User from 'components/User/User';
import { dateTimeToLocaleString } from 'helpers/DateToLocaleStringCoverters';
import { getUserId, isAdmin } from 'helpers/LocalStorageHelper';
import { showErrorToast } from 'helpers/showErrorToast';
import { useToast } from 'providers/ToastProvider';

type BanSectionProps = {
  banData: BanUser | null;
  userId: number;
};

const BanSection = ({ banData, userId }: BanSectionProps) => {
  const [reason, setReason] = useState<string>(banData?.reason || '');

  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const { mutateAsync: createBan, isPending: isCreating } = useMutation(
    userBanCreateMutation(userId),
  );
  const { mutateAsync: deleteBan, isPending: isDeleting } = useMutation(
    userBanDeleteMutation(userId),
  );

  const onCreate = async () => {
    await createBan({ reason })
      .then(async () => {
        showToast({
          detail: 'Felhasználó kitiltva',
          life: 3000,
          severity: 'success',
          summary: 'Siker',
        });

        await queryClient.invalidateQueries({
          queryKey: queryKeys.user(userId),
        });
      })
      .catch((error) => {
        showErrorToast(error);
      });
  };

  const onDelete = async () => {
    await deleteBan()
      .then(async () => {
        showToast({
          detail: 'Felhasználó kitiltása feloldva',
          life: 3000,
          severity: 'success',
          summary: 'Siker',
        });

        await queryClient.invalidateQueries({
          queryKey: queryKeys.user(userId),
        });
      })
      .catch((error) => {
        showErrorToast(error);
      });
  };

  return (
    <>
      <div className="font-semibold mt-3 text-900 text-lg">Kitiltás</div>
      <Divider />
      <div className="field">
        <label className="font-medium text-900" htmlFor="reason">
          Indoklás
        </label>
        <InputTextarea
          autoResize
          disabled={!!banData || !isAdmin() || getUserId() === userId}
          id="reason"
          name="reason"
          onChange={(e) => setReason(e.target.value)}
          rows={5}
          value={reason}
        />
      </div>
      {banData && (
        <div className="column-gap-5 flex flex-wrap">
          <div className="flex flex-column field">
            <label className="font-medium text-900">Kitiltás dátuma</label>
            <div className="pt-1">
              {dateTimeToLocaleString(new Date(banData.created), false)}
            </div>
          </div>
          <div className="field">
            <label className="font-medium text-900">Kitiltó</label>
            <User
              imageUrl={banData.creator.avatar_url}
              name={banData.creator.full_name}
            />
          </div>
        </div>
      )}
      <Button
        className="w-auto"
        disabled={!isAdmin() || getUserId() === userId}
        icon={banData ? 'pi pi-check' : 'pi pi-ban'}
        label={banData ? 'Kitiltás törlése' : 'Kitiltás'}
        severity={banData ? 'success' : 'danger'}
        loading={banData ? isDeleting : isCreating}
        onClick={banData ? () => onDelete() : () => onCreate()}
      />
    </>
  );
};

export default BanSection;
