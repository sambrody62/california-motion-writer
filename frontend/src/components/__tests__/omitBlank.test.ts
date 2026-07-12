/**
 * omitBlank drops the blank values that react-hook-form's retained store
 * re-registers around a step change, so they never shadow the condition
 * context or overwrite real answers accumulated in allAnswers on submit.
 */
import { omitBlank } from '../motion/omitBlank';

describe('omitBlank', () => {
  test('drops undefined, null, and empty-string values', () => {
    expect(
      omitBlank({ a: 'Yes', b: null, c: undefined, d: '', e: 0, f: false })
    ).toEqual({ a: 'Yes', e: 0, f: false });
  });

  test('drops falsy leaves from checkbox groups, and empty groups entirely', () => {
    expect(
      omitBlank({
        order_types: { 'Child support': false, Other: false },
        contact_types: { Phone: true, Email: false },
      })
    ).toEqual({ contact_types: { Phone: true } });
  });

  test('keeps arrays untouched', () => {
    expect(omitBlank({ exhibits: ['a.pdf'] })).toEqual({ exhibits: ['a.pdf'] });
  });
});
