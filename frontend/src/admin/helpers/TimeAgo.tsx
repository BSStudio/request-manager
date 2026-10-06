import { ComponentProps, useEffect, useRef } from 'react';

import { format, cancel, render } from 'timeago.js';
import type { Opts, TDate } from 'timeago.js/lib/interface';

/**
 * Converts input to a valid datetime string for the <time> tag
 * @see https://developer.mozilla.org/en-US/docs/Web/HTML/Element/time
 */
const toDateTime = (input: TDate): string => {
  return String(input instanceof Date ? input.getTime() : input);
};

interface TimeAgoProps extends ComponentProps<'time'> {
  datetime: TDate;
  live?: boolean;
  opts?: Opts;
  locale?: string;
}

function TimeAgo({
  datetime,
  live = true,
  locale,
  opts,
  ...timeProps
}: TimeAgoProps) {
  const timeRef = useRef<HTMLTimeElement>(null);

  useEffect(() => {
    const timeElement = timeRef.current;
    if (!timeElement) return;

    if (live) {
      timeElement.setAttribute('datetime', toDateTime(datetime));
      render(timeElement, locale, opts);
    }

    return () => {
      cancel(timeElement);
    };
  }, [datetime, live, locale, opts]);

  return (
    <time ref={timeRef} {...timeProps}>
      {format(datetime, locale, opts)}
    </time>
  );
}

export default TimeAgo;
