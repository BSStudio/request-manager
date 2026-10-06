import { useState } from 'react';

import { cn } from 'cn';
import { StarIcon } from 'lucide-react';

type StarRatingProps = {
  disabled?: boolean;
  onChange: (value: number) => void;
  value: number;
};

export default function StarRating({
  disabled,
  onChange,
  value,
}: StarRatingProps) {
  const [hovered, setHovered] = useState<number | null>(null);
  const shown = hovered ?? value;

  return (
    <div
      aria-label="Értékelés"
      className="-mx-1 flex"
      onPointerLeave={() => setHovered(null)}
      role="group"
    >
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          aria-label={`${star} csillag`}
          aria-pressed={star === value}
          className="rounded-md p-1 outline-none focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none"
          disabled={disabled}
          key={star}
          onClick={() => onChange(star)}
          // A tap would leave the hover stuck on touch screens.
          onPointerEnter={(event) =>
            event.pointerType === 'mouse' && setHovered(star)
          }
          type="button"
        >
          <StarIcon
            className={cn(
              'size-6 text-muted-foreground/50 transition-[color,fill,scale]',
              star <= shown && 'fill-warning text-warning',
              hovered !== null && star <= hovered && 'scale-110',
            )}
          />
        </button>
      ))}
    </div>
  );
}
