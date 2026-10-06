import { cn } from 'cn';
import { ArrowRightIcon, ClockIcon, UsersRoundIcon } from 'lucide-react';
import { Link } from 'react-router';

import SectionHeading from 'site/components/home/SectionHeading';
import { Button } from 'site/components/ui/button';

const steps = [
  {
    text: 'Legalább 8 nappal az esemény előtt, hétfőig. Bejelentkezve az adataidat sem kell újra megadnod.',
    title: 'Küldd be a felkérést',
  },
  {
    text: 'A heti gyűlésünkön eldöntjük, el tudjuk-e vállalni, és felvesszük veled a kapcsolatot.',
    title: 'Hétfőn döntünk',
  },
  {
    text: 'Stábunk ott lesz az eseményeden, és felveszi vagy élőben közvetíti azt.',
    title: 'Forgatunk',
  },
  {
    text: 'Ha publikáltuk, e\u2011mailben értesítünk, és bejelentkezve értékelheted is.',
    title: 'Elkészül a videó',
  },
];

const notes = [
  {
    icon: ClockIcon,
    text: 'Későn vagy hiányosan beküldött felkéréseket nem biztos, hogy el tudunk vállalni.',
    title: 'Időben küldd be',
  },
  {
    icon: UsersRoundIcon,
    text: 'A stúdió tagjai egyetemisták. Ha egy felkéréshez nincs elég emberünk vagy eszközünk, nem tudjuk elvállalni.',
    title: 'Diákok vagyunk',
  },
];

export default function ProcessSection() {
  return (
    <section
      className="scroll-mt-16 border-y bg-muted/50 py-24 sm:py-32"
      id="igy-mukodik"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <SectionHeading
          kicker="Így működik"
          title="A felkéréstől a kész videóig"
        />
        <ol className="mt-16 grid lg:grid-cols-4 lg:gap-6">
          {steps.map(({ text, title }, index) => (
            <li
              className="relative flex gap-5 pb-10 last:pb-0 lg:flex-col lg:gap-6 lg:pb-0"
              key={title}
            >
              <span
                aria-hidden
                className={cn(
                  'absolute top-12 bottom-0 left-6 w-px bg-border lg:top-6 lg:-right-6 lg:bottom-auto lg:left-12 lg:h-px lg:w-auto',
                  index === steps.length - 1 && 'hidden',
                )}
              />
              <span className="relative grid size-12 shrink-0 place-items-center rounded-full border border-primary/30 bg-background font-mono text-sm font-semibold text-primary shadow-sm">
                {String(index + 1).padStart(2, '0')}
              </span>
              <div className="pt-2.5 lg:pt-0 lg:pr-4">
                <h3 className="text-xl font-semibold">{title}</h3>
                <p className="mt-2 leading-relaxed text-muted-foreground">
                  {text}
                </p>
              </div>
            </li>
          ))}
        </ol>
        <div className="mt-16 grid gap-4 md:grid-cols-2">
          {notes.map(({ icon: Icon, text, title }) => (
            <div
              className="flex gap-4 rounded-2xl border bg-background p-6"
              key={title}
            >
              <Icon className="mt-0.5 size-5 shrink-0 text-primary" />
              <div>
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  {text}
                </p>
              </div>
            </div>
          ))}
        </div>
        <Button asChild className="mt-12" size="lg">
          <Link to="/new-request">
            Felkérés beküldése
            <ArrowRightIcon data-icon="inline-end" />
          </Link>
        </Button>
      </div>
    </section>
  );
}
