import { usePageTitle } from 'hooks/usePageTitle';
import ContactSection from 'site/components/home/ContactSection';
import HeroSection from 'site/components/home/HeroSection';
import ProcessSection from 'site/components/home/ProcessSection';
import ServicesSection from 'site/components/home/ServicesSection';

function HomePage() {
  usePageTitle();

  return (
    <>
      <HeroSection />
      <ServicesSection />
      <ProcessSection />
      <ContactSection />
    </>
  );
}

export { HomePage as Component };
