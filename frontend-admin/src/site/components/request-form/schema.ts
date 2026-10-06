import { z } from 'zod';

import { emailSchema, nameSchema, phoneSchema } from 'site/lib/person';

export const OTHER_TYPE = 'other';

// Accepts the usual ways of typing a time: 18:30, 18.30, 1830, 8:30 or 18.
export function parseTime(input: string) {
  const match = /^(\d{1,2})(?:[\s.,:]?(\d{2}))?$/.exec(input.trim());
  if (!match) return null;
  const [, hour, minute = '00'] = match;
  if (Number(hour) > 23 || Number(minute) > 59) return null;
  return `${hour.padStart(2, '0')}:${minute}`;
}

export function toDateTime(date: string, time: string) {
  const parsed = parseTime(time);
  return date && parsed ? new Date(`${date}T${parsed}`) : null;
}

const timeSchema = z
  .string()
  .min(1, 'Add meg az időpontot!')
  .refine((value) => parseTime(value) !== null, {
    message: 'Érvénytelen időpont, így add meg: 18:30',
  });

const maxLength = (max: number) => `Legfeljebb ${max} karakter lehet.`;

export const personalSchema = z.object({
  requesterEmail: emailSchema,
  requesterFirstName: nameSchema('Add meg a keresztneved!'),
  requesterLastName: nameSchema('Add meg a vezetékneved!'),
  requesterMobile: phoneSchema,
});

export const eventSchema = z
  .object({
    endDate: z.string().min(1, 'Válaszd ki a napot!'),
    endTime: timeSchema,
    place: z
      .string()
      .trim()
      .min(1, 'Add meg a helyszínt!')
      .max(150, maxLength(150)),
    startDate: z.string().min(1, 'Válaszd ki a napot!'),
    startTime: timeSchema,
    title: z
      .string()
      .trim()
      .min(1, 'Add meg az esemény nevét!')
      .max(200, maxLength(200)),
    type: z.string().min(1, 'Válaszd ki, milyen videót szeretnél!'),
    typeOther: z.string().trim().max(50, maxLength(50)),
  })
  .superRefine((values, context) => {
    if (values.type === OTHER_TYPE && !values.typeOther) {
      context.addIssue({
        code: 'custom',
        message: 'Írd le, milyen videót szeretnél!',
        path: ['typeOther'],
      });
    }
    const start = toDateTime(values.startDate, values.startTime);
    const end = toDateTime(values.endDate, values.endTime);
    if (start && start <= new Date()) {
      context.addIssue({
        code: 'custom',
        message: 'A kezdés nem lehet a múltban.',
        path: ['startTime'],
      });
    }
    if (start && end && end <= start) {
      context.addIssue({
        code: 'custom',
        message: 'A befejezés legyen később, mint a kezdés.',
        path: ['endTime'],
      });
    }
  });

export const notesSchema = z.object({
  comment: z.string(),
});

export type RequestFormValues = z.infer<typeof personalSchema> &
  z.infer<typeof eventSchema> &
  z.infer<typeof notesSchema>;

export const emptyValues: RequestFormValues = {
  comment: '',
  endDate: '',
  endTime: '',
  place: '',
  requesterEmail: '',
  requesterFirstName: '',
  requesterLastName: '',
  requesterMobile: '',
  startDate: '',
  startTime: '',
  title: '',
  type: '',
  typeOther: '',
};
