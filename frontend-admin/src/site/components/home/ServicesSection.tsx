import SectionHeading from 'site/components/home/SectionHeading';
import { requestTypes } from 'site/lib/requestTypes';

const [live, ...videos] = requestTypes;

function LiveCard() {
  const Icon = live.icon;

  return (
    <article className="relative isolate overflow-hidden rounded-3xl bg-ink p-8 text-white ring-1 ring-white/10 ring-inset sm:col-span-2 sm:p-10">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_85%_20%,color-mix(in_oklab,var(--primary)_55%,transparent),transparent_55%)]" />
      <div className="absolute inset-0 -z-10 bg-[repeating-linear-gradient(to_bottom,transparent_0_3px,rgb(255_255_255/0.035)_3px_4px)]" />
      <Icon
        aria-hidden
        className="absolute -right-6 -bottom-8 -z-10 size-56 text-white/[0.06]"
        strokeWidth={1.25}
      />
      <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 font-mono text-xs tracking-[0.2em] uppercase ring-1 ring-white/15">
        <span className="size-2 rounded-full bg-tally shadow-[0_0_10px_2px] shadow-tally/60 motion-safe:animate-pulse" />
        Élő
      </span>
      <h3 className="mt-6 text-3xl font-bold sm:text-4xl">{live.title}</h3>
      <p className="mt-3 max-w-md text-lg leading-relaxed text-white/70">
        {live.description}
      </p>
    </article>
  );
}

export default function ServicesSection() {
  return (
    <section className="scroll-mt-16 py-24 sm:py-32" id="szolgaltatasok">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <SectionHeading kicker="Szolgáltatások" title="Mit vállalunk?">
          A rendezvényed jellegétől függően videót készítünk róla, vagy élőben
          közvetítjük.
        </SectionHeading>
        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <LiveCard />
          {videos.map(({ description, icon: Icon, title }) => (
            <article
              className="group rounded-3xl border bg-card p-7 transition duration-300 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
              key={title}
            >
              <span className="grid size-12 place-items-center rounded-2xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <Icon className="size-5.5" />
              </span>
              <h3 className="mt-6 text-xl font-semibold">{title}</h3>
              <p className="mt-2 leading-relaxed text-muted-foreground">
                {description}
              </p>
            </article>
          ))}
        </div>
        <p className="mt-8 text-muted-foreground">
          Más elképzelésed van? A felkérésben leírhatod, mit szeretnél.
        </p>
      </div>
    </section>
  );
}
