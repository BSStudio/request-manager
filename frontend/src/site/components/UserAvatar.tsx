import { getInitials } from 'helpers/names';
import { type SessionUser } from 'helpers/session';
import { Avatar, AvatarFallback, AvatarImage } from 'site/components/ui/avatar';

type UserAvatarProps = {
  className?: string;
  size?: 'default' | 'sm' | 'lg';
  user: SessionUser;
};

export default function UserAvatar({ className, size, user }: UserAvatarProps) {
  return (
    <Avatar className={className} size={size}>
      <AvatarImage alt="" src={user.avatar} />
      <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
        {getInitials(user.name)}
      </AvatarFallback>
    </Avatar>
  );
}
