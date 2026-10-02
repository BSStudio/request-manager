import { MoonIcon, SunIcon } from 'lucide-react';

import { Button } from 'site/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from 'site/components/ui/tooltip';
import { useDarkMode } from 'site/hooks/useDarkMode';

export default function ThemeToggle({ className }: { className?: string }) {
  const [darkMode, setDarkMode] = useDarkMode();
  const label = darkMode ? 'Világos téma' : 'Sötét téma';

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          aria-label={label}
          className={className}
          onClick={() => setDarkMode(!darkMode)}
          size="icon"
          variant="ghost"
        >
          {darkMode ? <SunIcon /> : <MoonIcon />}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
