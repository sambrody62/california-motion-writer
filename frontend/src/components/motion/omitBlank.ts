/**
 * Drop blank values from a react-hook-form values snapshot. RHF v7 keeps
 * values after unmount (shouldUnregister: false), and around a step change
 * the previous step's fields re-register blank — so blanks in watch() or in
 * handleSubmit's whole-store data mean "unanswered here" and must never
 * shadow the condition context or overwrite real answers accumulated in
 * allAnswers. Checkbox groups are nested boolean objects: falsy leaves are
 * dropped, and a group left with nothing checked is dropped entirely.
 */
export function omitBlank(values: Record<string, any>): Record<string, any> {
  const kept: Record<string, any> = {};
  for (const [key, value] of Object.entries(values)) {
    if (value === undefined || value === null || value === '') continue;
    if (typeof value === 'object' && !Array.isArray(value)) {
      const checked = Object.fromEntries(
        Object.entries(value).filter(([, leaf]) => Boolean(leaf))
      );
      if (Object.keys(checked).length === 0) continue;
      kept[key] = checked;
    } else {
      kept[key] = value;
    }
  }
  return kept;
}
