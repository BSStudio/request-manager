import { forwardRef, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { AutoComplete } from 'primereact/autocomplete';
import type { AutoCompleteProps } from 'primereact/autocomplete';

import { UserAdminList } from 'api/models';
import { usersStaffListQuery } from 'api/queries';
import Avatar from 'components/Avatar/Avatar';
import { getUserId } from 'helpers/LocalStorageHelper';

const AutoCompleteStaff = forwardRef<
  React.Ref<HTMLInputElement>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  AutoCompleteProps<any, boolean>
>((props, ref) => {
  const { data = [] } = useQuery(usersStaffListQuery());
  const [filteredStaff, setFilteredStaff] = useState<UserAdminList[]>([]);

  const itemTemplate = (item: UserAdminList) => {
    return (
      <div className="align-items-center flex">
        <Avatar className="mr-2" image={item.avatar_url || undefined} />
        <div>{item.full_name}</div>
      </div>
    );
  };

  const searchStaff = (event: { query: string }) => {
    function moveOwnUserToTop(users: UserAdminList[]) {
      const index = users.findIndex(({ id }) => id === getUserId());
      if (index !== -1) {
        users.unshift(users.splice(index, 1)[0]);
      }
      return users;
    }

    function normalizeString(input: string) {
      return input
        .trim()
        .toLowerCase()
        .normalize('NFD')
        .replace(/\p{Diacritic}/gu, '');
    }

    let _filteredStaff;
    const _staff = moveOwnUserToTop([...data]);
    if (!event.query.trim().length) {
      _filteredStaff = [..._staff];
    } else {
      _filteredStaff = _staff.filter((user) => {
        const fullName = normalizeString(user.full_name);
        return fullName.includes(normalizeString(event.query));
      });
    }

    setFilteredStaff(_filteredStaff);
  };

  return (
    <AutoComplete
      completeMethod={searchStaff}
      dropdown
      field="full_name"
      forceSelection
      itemTemplate={itemTemplate}
      suggestions={filteredStaff}
      {...props}
      {...ref}
    />
  );
});

AutoCompleteStaff.displayName = 'AutoComplateStaff';

export default AutoCompleteStaff;
