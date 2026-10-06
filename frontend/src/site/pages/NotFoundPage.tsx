import { HouseIcon } from 'lucide-react';
import { Link } from 'react-router';

import NoSignal from 'site/components/NoSignal';
import { Button } from 'site/components/ui/button';
import { usePageTitle } from 'site/hooks/usePageTitle';

export default function NotFoundPage() {
  usePageTitle('Az oldal nem található');

  return (
    <NoSignal
      actions={
        <Button asChild size="lg">
          <Link to="/">
            <HouseIcon data-icon="inline-start" />
            Vissza a kezdőlapra
          </Link>
        </Button>
      }
      code="404 · Nincs jel"
      title="Adásszünet"
    >
      Az oldal, amit keresel, nem létezik vagy elköltözött. A hiba nem a te
      készülékedben van.
    </NoSignal>
  );
}
