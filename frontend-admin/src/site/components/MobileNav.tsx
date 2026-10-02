import { useState } from 'react';

import { cn } from 'cn';
import {
  HouseIcon,
  ListChecksIcon,
  LogInIcon,
  LogOutIcon,
  type LucideIcon,
  MenuIcon,
  MoonIcon,
  SendIcon,
  SunIcon,
  UserRoundIcon,
  WrenchIcon,
} from 'lucide-react';
import { NavLink } from 'react-router';

import BssLogo from 'site/components/BssLogo';
import SocialLinks from 'site/components/SocialLinks';
import { Button } from 'site/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from 'site/components/ui/sheet';
import UserAvatar from 'site/components/UserAvatar';
import { useDarkMode } from 'site/hooks/useDarkMode';
import { useSignOut } from 'site/hooks/useSignOut';
import type { SessionUser } from 'site/lib/session';

type NavItem = { icon: LucideIcon; label: string; to: string };

const linkClassName =
  'flex h-12 items-center gap-3 rounded-lg px-3 font-medium transition-colors hover:bg-muted [&_svg]:size-5 [&_svg]:text-muted-foreground';

const themes = [
  { dark: false, icon: SunIcon, label: 'Világos' },
  { dark: true, icon: MoonIcon, label: 'Sötét' },
];

type MobileNavProps = {
  className?: string;
  user: SessionUser | null;
};

export default function MobileNav({ className, user }: MobileNavProps) {
  const [open, setOpen] = useState(false);
  const [darkMode, setDarkMode] = useDarkMode();
  const handleSignOut = useSignOut();

  const items: NavItem[] = [
    { icon: HouseIcon, label: 'Kezdőlap', to: '/' },
    { icon: SendIcon, label: 'Felkérés beküldése', to: '/new-request' },
    ...(user
      ? [
          { icon: ListChecksIcon, label: 'Felkéréseim', to: '/my-requests' },
          { icon: UserRoundIcon, label: 'Profilom', to: '/profile' },
        ]
      : [{ icon: LogInIcon, label: 'Bejelentkezés', to: '/login' }]),
  ];

  return (
    <Sheet onOpenChange={setOpen} open={open}>
      <SheetTrigger asChild>
        <Button
          aria-label="Menü megnyitása"
          className={className}
          size="icon-lg"
          variant="ghost"
        >
          <MenuIcon className="size-6" />
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[85%] gap-0" side="right">
        <SheetHeader className="border-b px-5 py-4">
          <SheetTitle className="flex items-center gap-3">
            <BssLogo className="h-6 w-auto" />
            <span className="border-l pl-3 font-semibold">Felkéréskezelő</span>
          </SheetTitle>
          <SheetDescription className="sr-only">Navigáció</SheetDescription>
        </SheetHeader>
        {user && (
          <div className="flex items-center gap-3 px-5 pt-5 pb-2">
            <UserAvatar size="lg" user={user} />
            <div className="min-w-0">
              <p className="truncate font-medium">{user.name}</p>
              <p className="text-sm text-muted-foreground">Bejelentkezve</p>
            </div>
          </div>
        )}
        <nav className="flex flex-col gap-1 p-3">
          {items.map(({ icon: Icon, label, to }) => (
            <NavLink
              className={({ isActive }) =>
                cn(linkClassName, isActive && 'bg-muted text-primary')
              }
              end
              key={to}
              onClick={() => setOpen(false)}
              to={to}
            >
              <Icon />
              {label}
            </NavLink>
          ))}
          {user?.isPrivileged && (
            <a className={linkClassName} href="/admin">
              <WrenchIcon />
              Admin felület
            </a>
          )}
        </nav>
        <div className="mt-auto space-y-4 border-t p-5">
          <div
            aria-label="Megjelenés"
            className="grid grid-cols-2 rounded-full bg-muted p-1"
            role="group"
          >
            {themes.map(({ dark, icon: Icon, label }) => (
              <button
                aria-pressed={darkMode === dark}
                className={cn(
                  'flex items-center justify-center gap-1.5 rounded-full py-2 text-sm text-muted-foreground transition-colors',
                  darkMode === dark &&
                    'bg-background text-foreground shadow-sm',
                )}
                key={label}
                onClick={() => setDarkMode(dark)}
                type="button"
              >
                <Icon className="size-4" />
                {label}
              </button>
            ))}
          </div>
          {user && (
            <Button
              className="w-full"
              onClick={() => {
                setOpen(false);
                void handleSignOut();
              }}
              size="lg"
              variant="outline"
            >
              <LogOutIcon />
              Kijelentkezés
            </Button>
          )}
          <SocialLinks className="justify-center pt-1" />
        </div>
      </SheetContent>
    </Sheet>
  );
}
