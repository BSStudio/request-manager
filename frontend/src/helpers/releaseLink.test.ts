import { describe, expect, it } from 'vitest';

import { releaseLink } from 'helpers/releaseLink';

describe('releaseLink', () => {
  it('links a tag build to its release', () => {
    expect(releaseLink('1.4.0')).toEqual({
      label: 'v1.4.0',
      url: 'https://github.com/BSStudio/request-manager/releases/tag/v1.4.0',
    });
  });

  it('links any other image to its commit', () => {
    expect(releaseLink('0.0.0+abc1234')).toEqual({
      label: 'abc1234',
      url: 'https://github.com/BSStudio/request-manager/commit/abc1234',
    });
  });

  it('links a local build to the repository', () => {
    expect(releaseLink('dev')).toEqual({
      label: 'dev',
      url: 'https://github.com/BSStudio/request-manager',
    });
  });
});
