// CA court holidays are out of scope — only weekends are skipped.
// Courts may observe additional holidays; users should verify with their court.

/**
 * Advance a date by n court days (skipping Saturdays and Sundays).
 * Each weekday landed on counts as one court day.
 * If n is 0 and startDate is a weekday, the startDate is returned unchanged.
 * If startDate is a weekend, n=0 still returns startDate (the caller decides
 * whether to use the raw date or advance — callers providing service dates
 * should use n >= 1).
 *
 * CA court holidays are out of scope — only weekends are skipped.
 */
export function addCourtDays(startDate: Date, days: number): Date {
  if (days === 0) {
    return new Date(startDate);
  }

  const result = new Date(startDate);
  let counted = 0;

  while (counted < days) {
    result.setDate(result.getDate() + 1);
    const dayOfWeek = result.getDay();
    // 0 = Sunday, 6 = Saturday
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      counted++;
    }
  }

  return result;
}

/**
 * Format a Date as a human-readable string for the deadline warning.
 */
export function formatCourtDeadline(date: Date): string {
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}
