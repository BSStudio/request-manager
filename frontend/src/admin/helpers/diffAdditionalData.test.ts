import { describe, expect, it } from 'vitest';

import { diffAdditionalData } from 'admin/helpers/diffAdditionalData';

describe('diffAdditionalData', () => {
  it('keeps only the changed and added keys', () => {
    expect(
      diffAdditionalData(
        { accepted: true, length: 125 },
        { accepted: true, editing_done: true, length: 130 },
      ),
    ).toEqual({ editing_done: true, length: 130 });
  });

  it('keeps only the changed keys of nested objects', () => {
    expect(
      diffAdditionalData(
        { recording: { copied_to_gdrive: true, path: 'N://a' } },
        { recording: { copied_to_gdrive: true, path: 'N://b' } },
      ),
    ).toEqual({ recording: { path: 'N://b' } });
  });

  it('sends a removed key as null', () => {
    expect(
      diffAdditionalData(
        { canceled: true, recording: { path: 'N://a', removed: true } },
        { recording: { path: 'N://a' } },
      ),
    ).toEqual({ canceled: null, recording: { removed: null } });
  });

  it('takes null for a missing key', () => {
    expect(
      diffAdditionalData({ accepted: true }, { accepted: true, failed: null }),
    ).toEqual({});
  });

  it('replaces a changed list as a whole', () => {
    expect(
      diffAdditionalData(
        { aired: ['2026-10-01'] },
        { aired: ['2026-10-01', '2026-10-15'] },
      ),
    ).toEqual({ aired: ['2026-10-01', '2026-10-15'] });
  });

  it('leaves anything but an object as it is', () => {
    expect(diffAdditionalData({ accepted: true }, ['accepted'])).toEqual([
      'accepted',
    ]);
  });

  it('returns nothing when nothing changed', () => {
    expect(
      diffAdditionalData(
        { aired: ['2026-10-01'], recording: { path: 'N://a' } },
        { aired: ['2026-10-01'], recording: { path: 'N://a' } },
      ),
    ).toEqual({});
  });
});
