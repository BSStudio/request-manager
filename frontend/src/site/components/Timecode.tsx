import { useEffect, useRef } from 'react';

const FRAMES_PER_SECOND = 25;

function formatTimecode(frames: number) {
  const seconds = Math.floor(frames / FRAMES_PER_SECOND);
  return [
    Math.floor(seconds / 3600),
    Math.floor(seconds / 60) % 60,
    seconds % 60,
    frames % FRAMES_PER_SECOND,
  ]
    .map((value) => String(value).padStart(2, '0'))
    .join(':');
}

export default function Timecode({ className }: { className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const start = performance.now();
    let frame = requestAnimationFrame(function tick(now) {
      // Writes the DOM directly, a re-render every frame is not worth it.
      if (ref.current) {
        ref.current.textContent = formatTimecode(
          Math.floor(((now - start) / 1000) * FRAMES_PER_SECOND),
        );
      }
      frame = requestAnimationFrame(tick);
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <span className={className} ref={ref}>
      {formatTimecode(0)}
    </span>
  );
}
