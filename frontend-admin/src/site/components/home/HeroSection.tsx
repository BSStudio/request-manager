import { cn } from 'cn';
import { ArrowRightIcon, ClockIcon, PlayIcon } from 'lucide-react';
import { Link } from 'react-router';

import studioImage from 'site/assets/studio.webp';
import Timecode from 'site/components/Timecode';
import { Button } from 'site/components/ui/button';

function Viewfinder() {
  const corner = 'absolute size-7 border-white/40 sm:size-10';

  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-3 top-[calc(4.75rem+env(safe-area-inset-top))] bottom-3 font-mono text-[0.6875rem] tracking-[0.14em] sm:inset-x-6 sm:top-[calc(5.5rem+env(safe-area-inset-top))] sm:bottom-6"
    >
      <span className={cn(corner, 'top-0 left-0 border-t-2 border-l-2')} />
      <span className={cn(corner, 'top-0 right-0 border-t-2 border-r-2')} />
      <span className={cn(corner, 'bottom-0 left-0 border-b-2 border-l-2')} />
      <span className={cn(corner, 'right-0 bottom-0 border-r-2 border-b-2')} />
      <div className="absolute top-3 left-4 flex items-center gap-2 text-white/85 sm:top-4 sm:left-6">
        <span className="size-2 rounded-full bg-tally shadow-[0_0_10px_2px] shadow-tally/60 motion-safe:animate-pulse" />
        REC
        <Timecode className="ml-1 text-white/60 tabular-nums" />
      </div>
      <div className="absolute top-3 right-4 text-white/55 sm:top-4 sm:right-6">
        CAM A · 25P
      </div>
    </div>
  );
}

export default function HeroSection() {
  return (
    <section className="relative isolate flex min-h-svh flex-col overflow-hidden bg-ink text-white">
      <img
        alt=""
        className="absolute inset-0 -z-30 size-full object-cover opacity-55 motion-safe:animate-ken-burns"
        fetchPriority="high"
        src={studioImage}
      />
      <div className="absolute inset-0 -z-20 bg-[linear-gradient(to_top,var(--ink)_6%,transparent_55%),linear-gradient(to_right,color-mix(in_oklab,var(--ink)_80%,transparent)_10%,transparent_80%)]" />
      <div className="absolute inset-0 -z-10 bg-grain opacity-[0.08] mix-blend-overlay" />
      <Viewfinder />
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center px-6 pt-36 pb-24 sm:px-12 sm:pt-40">
        <p className="flex animate-in items-center gap-3 font-mono text-xs tracking-[0.2em] text-white/70 uppercase duration-700 fade-in">
          <span className="h-px w-8 bg-white/40" />
          Budavári Schönherz Stúdió
        </p>
        <h1 className="mt-6 max-w-4xl animate-in text-[clamp(2.25rem,9vw,5.75rem)] leading-[0.95] font-bold duration-700 fade-in slide-in-from-bottom-4">
          Te szervezed,
          <br />
          <span className="bg-linear-to-r from-sky-300 via-blue-300 to-indigo-200 bg-clip-text text-transparent">
            mi megörökítjük.
          </span>
        </h1>
        <p className="mt-7 max-w-xl animate-in text-lg leading-relaxed text-white/75 delay-150 duration-700 fill-mode-both fade-in slide-in-from-bottom-4 sm:text-xl">
          Videót készítünk és élőben közvetítünk a Schönherz Kollégium és a
          BME-VIK eseményeiről. Küldd be a felkérésed, és a hétfői gyűlésünkön
          döntünk róla.
        </p>
        <div className="mt-10 flex animate-in flex-col gap-3 delay-300 duration-700 fill-mode-both fade-in slide-in-from-bottom-4 sm:flex-row">
          <Button
            asChild
            className="bg-white text-ink shadow-[0_0_40px_-8px] shadow-sky-300/60 hover:bg-white/85"
            size="xl"
          >
            <Link to="/new-request">
              Felkérés beküldése
              <ArrowRightIcon data-icon="inline-end" />
            </Link>
          </Button>
          <Button
            asChild
            className="border-white/25 bg-white/5 text-white backdrop-blur-sm hover:bg-white/15 hover:text-white dark:border-white/25 dark:bg-white/5 dark:hover:bg-white/15"
            size="xl"
            variant="outline"
          >
            <a
              href="https://bsstudio.hu/video/latest"
              rel="noreferrer"
              target="_blank"
            >
              <PlayIcon data-icon="inline-start" />
              Korábbi videóink
            </a>
          </Button>
        </div>
        <p className="mt-8 flex animate-in items-center gap-2 text-sm text-white/60 delay-500 duration-700 fill-mode-both fade-in">
          <ClockIcon className="size-4" />
          Legalább 8 nappal az esemény előtt, hétfőig küldd be a felkérést.
        </p>
      </div>
    </section>
  );
}
