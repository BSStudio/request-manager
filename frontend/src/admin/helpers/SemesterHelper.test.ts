import { afterEach, describe, expect, it, vi } from 'vitest';

import { getLatestSemester, getSemesters } from 'admin/helpers/SemesterHelper';

function semestersOn(date: Date) {
  vi.useFakeTimers();
  vi.setSystemTime(date);
  return getSemesters();
}

describe('getSemesters', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('lists the newest first, from the autumn semester on', () => {
    const names = semestersOn(new Date(2026, 9, 12)).map(({ name }) => name);

    expect(names.slice(0, 3)).toEqual(['Későbbi', '2026/27/1', '2025/26/2']);
    expect(names.slice(-3)).toEqual(['2021/22/2', '2021/22/1', 'Korábbi']);
  });

  it('starts the autumn semester only in July', () => {
    const [later, latest] = semestersOn(new Date(2026, 5, 30));

    expect(latest.name).toBe('2025/26/2');
    expect(later.afterDate).toEqual(new Date('2026-07-01'));
    expect(semestersOn(new Date(2026, 6, 1))[1].name).toBe('2026/27/1');
  });

  it('leaves no gap between semesters', () => {
    const semesters = semestersOn(new Date(2026, 9, 12)).reverse();

    semesters.slice(1).forEach((semester, index) => {
      const dayAfter = new Date(semesters[index].beforeDate);
      dayAfter.setDate(dayAfter.getDate() + 1);
      expect(semester.afterDate).toEqual(dayAfter);
    });
  });
});

describe('getLatestSemester', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('is the current semester', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 2, 1));

    expect(getLatestSemester().name).toBe('2025/26/2');
  });
});
