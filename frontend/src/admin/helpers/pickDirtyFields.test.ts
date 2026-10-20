import { describe, expect, it } from 'vitest';

import { pickDirtyFields } from 'admin/helpers/pickDirtyFields';

describe('pickDirtyFields', () => {
  it('keeps only the dirty fields', () => {
    expect(
      pickDirtyFields(
        { place: 'Aula', responsible: null, title: 'Gólyabál' },
        { responsible: true, title: true },
      ),
    ).toEqual({ responsible: null, title: 'Gólyabál' });
  });

  it('keeps only the dirty keys of nested objects', () => {
    expect(
      pickDirtyFields(
        {
          additional_data: {
            coding: { website: true },
            length: 125,
            publishing: { website: 'https://bss.hu' },
          },
          title: 'Gólyabál',
        },
        { additional_data: { coding: { website: true }, length: true } },
      ),
    ).toEqual({ additional_data: { coding: { website: true }, length: 125 } });
  });

  it('keeps a whole object or list marked dirty as one field', () => {
    expect(
      pickDirtyFields(
        { assignees: [1, 2], editor: { id: 3 } },
        { assignees: [true, true], editor: true },
      ),
    ).toEqual({ assignees: [1, 2], editor: { id: 3 } });
  });

  it('returns nothing when nothing changed', () => {
    expect(pickDirtyFields({ title: 'Gólyabál' }, {})).toEqual({});
  });
});
