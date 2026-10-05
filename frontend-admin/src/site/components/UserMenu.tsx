import { cn } from 'cn';
import {
  ChevronDownIcon,
  DownloadIcon,
  ListChecksIcon,
  LogOutIcon,
  UserRoundIcon,
  WrenchIcon,
} from 'lucide-react';
import { Link } from 'react-router';

import { promptInstall, useCanInstall } from 'helpers/pwa';
import { Button } from 'site/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'site/components/ui/dropdown-menu';
import UserAvatar from 'site/components/UserAvatar';
import { useSignOut } from 'site/hooks/useSignOut';
import type { SessionUser } from 'site/lib/session';

type UserMenuProps = {
  className?: string;
  user: SessionUser;
};

export default function UserMenu({ className, user }: UserMenuProps) {
  const handleSignOut = useSignOut();
  const canInstall = useCanInstall();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          className={cn('gap-2 rounded-full pr-3 pl-1', className)}
          variant="ghost"
        >
          <UserAvatar size="sm" user={user} className="size-7" />
          <span className="max-w-36 truncate">{user.name}</span>
          <ChevronDownIcon className="opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex items-center gap-2.5 py-2">
          <UserAvatar user={user} />
          <span className="truncate text-sm text-foreground">{user.name}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/my-requests">
            <ListChecksIcon />
            Felkéréseim
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/profile">
            <UserRoundIcon />
            Profilom
          </Link>
        </DropdownMenuItem>
        {user.isPrivileged && (
          <DropdownMenuItem asChild>
            <a href="/admin">
              <WrenchIcon />
              Admin felület
            </a>
          </DropdownMenuItem>
        )}
        {canInstall && (
          <DropdownMenuItem onSelect={() => void promptInstall()}>
            <DownloadIcon />
            Alkalmazás telepítése
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void handleSignOut()}>
          <LogOutIcon />
          Kijelentkezés
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
