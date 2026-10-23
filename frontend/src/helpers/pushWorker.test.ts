import { describe, expect, it } from 'vitest';

import { base64UrlToUint8Array, windowFor } from 'helpers/pushWorker';

describe('base64UrlToUint8Array', () => {
  it('decodes the unpadded URL-safe alphabet', () => {
    expect([...base64UrlToUint8Array('-_8')]).toEqual([251, 255]);
  });
});

describe('windowFor', () => {
  const site = { url: 'https://felkeres.bsstudio.hu/my-requests' };
  const admin = { url: 'https://felkeres.bsstudio.hu/admin/requests/3' };

  it('reuses a window of the same app', () => {
    expect(windowFor([site, admin], '/admin/requests/5')).toBe(admin);
    expect(windowFor([admin, site], '/my-requests/5')).toBe(site);
  });

  it('never reuses a window of the other app', () => {
    expect(windowFor([admin], '/my-requests/5')).toBeUndefined();
  });
});
