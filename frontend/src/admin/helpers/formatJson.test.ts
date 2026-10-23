import { describe, expect, it } from 'vitest';

import { formatJson } from 'admin/helpers/formatJson';

describe('formatJson', () => {
  it('indents JSON', () => {
    expect(formatJson('{"name":"O\'Neil"}')).toBe('{\n  "name": "O\'Neil"\n}');
  });

  it('keeps text that is not JSON', () => {
    expect(formatJson("{'editing_done': True}")).toBe("{'editing_done': True}");
  });
});
