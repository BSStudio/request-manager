import { forwardRef } from 'react';

import type { AutoCompleteProps } from 'primereact/autocomplete';

import Avatar from 'admin/components/Avatar/Avatar';
import { UserAdminList } from 'api/models';

import AutoCompleteStaff from './AutoCompleteStaff';

const AutoCompleteStaffMultiple = forwardRef<
  React.Ref<HTMLInputElement>,
  AutoCompleteProps
>((props, ref) => {
  const selectedItemTemplate = (item: UserAdminList) => {
    return (
      <div className="align-items-center flex h-1rem">
        <Avatar
          className="mr-2 -ml-3"
          image={item.avatar_url || undefined}
          name={item.full_name}
        />
        <div>{item.full_name}</div>
      </div>
    );
  };

  return (
    <AutoCompleteStaff
      dropdown={false}
      forceSelection={false}
      multiple
      pt={{ token: { className: 'pr-1' } }}
      selectedItemTemplate={selectedItemTemplate}
      {...props}
      {...ref}
    />
  );
});

AutoCompleteStaffMultiple.displayName = 'AutoComplateStaffMultiple';

export default AutoCompleteStaffMultiple;
