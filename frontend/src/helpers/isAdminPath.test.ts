import { describe, expect, it } from 'vitest';

import { isAdminPath } from 'helpers/isAdminPath';

describe('isAdminPath', () => {
  it.each(['/admin', '/admin/', '/admin/requests/12'])(
    'matches %s',
    (pathname) => {
      expect(isAdminPath(pathname)).toBe(true);
    },
  );

  it.each(['/', '/administration', '/my-requests/admin'])(
    'does not match %s',
    (pathname) => {
      expect(isAdminPath(pathname)).toBe(false);
    },
  );
});
