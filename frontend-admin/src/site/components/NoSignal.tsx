import type { ReactNode } from 'react';

// SMPTE colour bars, the picture a broadcast shows when there is no signal.
const topBars = [
  '#c0c0c0',
  '#c0c000',
  '#00c0c0',
  '#00c000',
  '#c000c0',
  '#c00000',
  '#0000c0',
];
const middleBars = [
  '#0000c0',
  '#131313',
  '#c000c0',
  '#131313',
  '#00c0c0',
  '#131313',
  '#c0c0c0',
];
const bottomBars = ['#00214c', '#ffffff', '#32006a', '#131313'];

type NoSignalProps = {
  actions: ReactNode;
  children: ReactNode;
  code: string;
  title: string;
};

export default function NoSignal({
  actions,
  children,
  code,
  title,
}: NoSignalProps) {
  return (
    <section className="relative isolate flex min-h-svh flex-1 items-center justify-center overflow-hidden bg-ink px-4 py-28 text-white">
      <div
        aria-hidden
        className="absolute inset-0 -z-20 grid grid-rows-[67fr_8fr_25fr] opacity-80"
      >
        <div className="grid grid-cols-7">
          {topBars.map((color) => (
            <span key={color} style={{ background: color }} />
          ))}
        </div>
        <div className="grid grid-cols-7">
          {middleBars.map((color, index) => (
            <span key={index} style={{ background: color }} />
          ))}
        </div>
        <div className="grid grid-cols-[5fr_5fr_5fr_20fr]">
          {bottomBars.map((color) => (
            <span key={color} style={{ background: color }} />
          ))}
        </div>
      </div>
      <div
        aria-hidden
        className="absolute inset-0 -z-10 bg-grain opacity-30 mix-blend-overlay motion-safe:animate-static"
      />
      <div aria-hidden className="absolute inset-0 -z-10 bg-ink/45" />
      <div className="w-full max-w-md animate-in rounded-3xl bg-ink/85 p-8 text-center shadow-2xl ring-1 ring-white/10 backdrop-blur-md duration-500 fade-in zoom-in-95 sm:p-10">
        <p className="font-mono text-xs tracking-[0.3em] text-white/50 uppercase">
          {code}
        </p>
        <h1 className="mt-3 text-4xl font-bold sm:text-5xl">{title}</h1>
        <div className="mt-4 text-white/70">{children}</div>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          {actions}
        </div>
      </div>
    </section>
  );
}
