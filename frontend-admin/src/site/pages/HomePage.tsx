import HeroSection from 'site/components/home/HeroSection';
import { usePageTitle } from 'site/hooks/usePageTitle';

function HomePage() {
  usePageTitle();

  return <HeroSection />;
}

export { HomePage as Component };
