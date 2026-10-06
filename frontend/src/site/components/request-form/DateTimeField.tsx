import { type Ref, useState } from 'react';

import { cn } from 'cn';
import { format, isThisYear, parseISO } from 'date-fns';
import { CalendarIcon } from 'lucide-react';
import { hu } from 'react-day-picker/locale';

import { parseTime } from 'site/components/request-form/schema';
import { Button } from 'site/components/ui/button';
import { Calendar } from 'site/components/ui/calendar';
import { Input } from 'site/components/ui/input';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from 'site/components/ui/popover';

type DateTimeFieldProps = {
  date: string;
  dateInvalid?: boolean;
  dateRef?: Ref<HTMLButtonElement>;
  id: string;
  labelId: string;
  onDateChange: (date: string) => void;
  onTimeChange: (time: string) => void;
  time: string;
  timeInvalid?: boolean;
  timeRef?: Ref<HTMLInputElement>;
};

export default function DateTimeField({
  date,
  dateInvalid,
  dateRef,
  id,
  labelId,
  onDateChange,
  onTimeChange,
  time,
  timeInvalid,
  timeRef,
}: DateTimeFieldProps) {
  const [open, setOpen] = useState(false);
  const selected = date ? parseISO(date) : undefined;
  const today = new Date();

  return (
    <div className="flex gap-2">
      <Popover onOpenChange={setOpen} open={open}>
        <PopoverTrigger asChild>
          <Button
            aria-invalid={dateInvalid}
            aria-labelledby={`${labelId} ${id}-value`}
            className={cn(
              // The button base class would stop it from shrinking for long dates.
              'h-10 min-w-0 flex-1 shrink justify-start px-3 text-base font-normal md:text-sm',
              !selected && 'text-muted-foreground',
            )}
            id={id}
            ref={dateRef}
            variant="outline"
          >
            <CalendarIcon className="text-muted-foreground" />
            <span className="truncate" id={`${id}-value`}>
              {selected
                ? format(
                    selected,
                    isThisYear(selected)
                      ? 'MMM d., EEEE'
                      : 'yyyy. MMM d., EEEE',
                    { locale: hu },
                  )
                : 'Válassz napot'}
            </span>
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-auto p-0">
          <Calendar
            className="[--cell-size:--spacing(10)]"
            defaultMonth={selected ?? today}
            disabled={{ before: today }}
            locale={hu}
            mode="single"
            onSelect={(day) => {
              onDateChange(day ? format(day, 'yyyy-MM-dd') : '');
              setOpen(false);
            }}
            selected={selected}
          />
        </PopoverContent>
      </Popover>
      <Input
        aria-invalid={timeInvalid}
        aria-labelledby={labelId}
        autoComplete="off"
        className="w-28 shrink-0"
        id={`${id}-time`}
        inputMode="numeric"
        onBlur={() => {
          const parsed = parseTime(time);
          if (parsed && parsed !== time) onTimeChange(parsed);
        }}
        onChange={(event) => onTimeChange(event.target.value)}
        placeholder="pl. 18:30"
        ref={timeRef}
        value={time}
      />
    </div>
  );
}
