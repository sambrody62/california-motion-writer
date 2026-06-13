import { addCourtDays, formatCourtDeadline } from '../courtDays';

// Helper: create a local date (avoids UTC offset shifting the day)
const localDate = (year: number, month: number, day: number) =>
  new Date(year, month - 1, day);

const toLocalISO = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${dd}`;
};

describe('addCourtDays', () => {
  // Friday Jan 9 2026 + 9 court days
  // Mon Jan 12(1), Tue Jan 13(2), Wed Jan 14(3), Thu Jan 15(4), Fri Jan 16(5)
  // skip Sat/Sun
  // Mon Jan 19(6), Tue Jan 20(7), Wed Jan 21(8), Thu Jan 22(9) = Jan 22
  test('Friday + 9 court days = Thursday two weeks later', () => {
    const friday = localDate(2026, 1, 9); // Friday Jan 9 2026
    const result = addCourtDays(friday, 9);
    expect(toLocalISO(result)).toBe('2026-01-22');
  });

  test('Monday + 9 court days = Friday of the week after next', () => {
    const monday = localDate(2026, 1, 12); // Monday Jan 12 2026
    const result = addCourtDays(monday, 9);
    // Day 1=Tue 13, Day 2=Wed 14, Day 3=Thu 15, Day 4=Fri 16
    // skip Sat/Sun
    // Day 5=Mon 19, Day 6=Tue 20, Day 7=Wed 21, Day 8=Thu 22, Day 9=Fri 23
    expect(toLocalISO(result)).toBe('2026-01-23');
  });

  test('adds 0 court days returns same date', () => {
    const monday = localDate(2026, 1, 12);
    const result = addCourtDays(monday, 0);
    expect(toLocalISO(result)).toBe('2026-01-12');
  });

  test('Saturday input: first court day counted is Monday', () => {
    const saturday = localDate(2026, 1, 10); // Saturday Jan 10 2026
    const result = addCourtDays(saturday, 1);
    // Sat Jan 10 → skip Sun Jan 11 → Mon Jan 12 (count 1)
    expect(toLocalISO(result)).toBe('2026-01-12');
  });

  test('handles span across multiple weekends correctly', () => {
    const wednesday = localDate(2026, 1, 7); // Wednesday Jan 7 2026
    const result = addCourtDays(wednesday, 9);
    // Day 1=Thu 8, Day 2=Fri 9, [skip Sat/Sun]
    // Day 3=Mon 12, Day 4=Tue 13, Day 5=Wed 14, Day 6=Thu 15, Day 7=Fri 16
    // [skip Sat/Sun]
    // Day 8=Mon 19, Day 9=Tue 20
    expect(toLocalISO(result)).toBe('2026-01-20');
  });
});

describe('formatCourtDeadline', () => {
  test('returns a human-readable date string', () => {
    const date = new Date('2026-01-22');
    const result = formatCourtDeadline(date);
    expect(result).toContain('2026');
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });
});
