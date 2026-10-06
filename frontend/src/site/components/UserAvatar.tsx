import { cn } from 'cn';

import { getAvatarStyle, getInitials } from 'helpers/avatar';
import { Avatar, AvatarFallback, AvatarImage } from 'site/components/ui/avatar';

type UserAvatarProps = {
  className?: string;
  size?: 'default' | 'sm' | 'lg';
  user: { avatar?: string | null; name: string };
};

export default function UserAvatar({ className, size, user }: UserAvatarProps) {
  return (
    <Avatar className={cn('@container', className)} size={size}>
      <AvatarImage alt="" src={user.avatar || undefined} />
      <AvatarFallback
        className="text-[length:43.75cqw] font-medium select-none group-data-[size=sm]/avatar:text-[length:43.75cqw]"
        style={getAvatarStyle(user.name)}
      >
        {getInitials(user.name)}
      </AvatarFallback>
    </Avatar>
  );
}
