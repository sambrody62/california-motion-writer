/**
 * Tests for navigateAfterIntake routing helper
 */
import { navigateAfterIntake } from '../motion/intakeNavigation';

test('calls onComplete and navigates to preview with llmFailed state', () => {
  const navigate = jest.fn();
  const onComplete = jest.fn();

  navigateAfterIntake(navigate as any, 'motion-1', null, true, onComplete);

  expect(onComplete).toHaveBeenCalledWith('motion-1');
  expect(navigate).toHaveBeenCalledWith('/motion/motion-1/preview', {
    state: { llmFailed: true },
  });
});

test('returns to FormExecution with completed index when launched from it', () => {
  const navigate = jest.fn();
  const locationState = { fromFormExecution: true, formExecutionFormIndex: 2 };

  navigateAfterIntake(navigate as any, 'motion-1', locationState, false);

  expect(navigate).toHaveBeenCalledWith('/case/forms', {
    state: { ...locationState, completedFormIndex: 2 },
  });
});
