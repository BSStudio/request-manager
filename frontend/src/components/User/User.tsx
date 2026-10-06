import { classNames } from 'primereact/utils';

import Avatar from 'components/Avatar/Avatar';

interface UserProps {
  className?: string;
  imageUrl?: string;
  name: string;
}

const User = ({ className, imageUrl, name }: UserProps) => {
  return (
    <div className={classNames('align-items-center flex', className)}>
      <Avatar className="mr-2" image={imageUrl || undefined} />
      <div className="white-space-nowrap">{name}</div>
    </div>
  );
};

export default User;
