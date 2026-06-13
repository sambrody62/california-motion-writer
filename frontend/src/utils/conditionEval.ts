/**
 * Evaluate a simple condition string against a context object.
 * Supports: ==, !=, >, &&, ||, dot notation for checkbox keys.
 * Falls back to true if the expression cannot be parsed.
 */
export function evalCondition(
  condition: string,
  context: Record<string, any>
): boolean {
  // Handle && (AND) — split on && first, all clauses must be true
  if (condition.includes('&&')) {
    return condition.split('&&').every(clause => evalCondition(clause.trim(), context));
  }

  // Handle || (OR) — split on ||, any clause true is sufficient
  if (condition.includes('||')) {
    return condition.split('||').some(clause => evalCondition(clause.trim(), context));
  }

  // Handle != (not equal)
  if (condition.includes('!=')) {
    const [field, value] = condition.split('!=').map(s => s.trim().replace(/['"]/g, ''));
    return context[field] !== value;
  }

  // Handle == (equal)
  if (condition.includes('==')) {
    const [field, value] = condition.split('==').map(s => s.trim().replace(/['"]/g, ''));
    return context[field] === value;
  }

  // Handle > (greater than)
  if (condition.includes('>')) {
    const [field, value] = condition.split('>').map(s => s.trim());
    return Number(context[field]) > Number(value);
  }

  // Handle dot notation for checkbox keys like 'order_types.Other'
  if (condition.includes('.')) {
    const [field, property] = condition.split('.');
    return Boolean(context[field] && context[field][property]);
  }

  // Default: show the question
  return true;
}
