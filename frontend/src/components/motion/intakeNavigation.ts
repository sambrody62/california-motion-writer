import { NavigateFunction } from 'react-router-dom';

// Post-intake routing: back to FormExecution when it launched us, else preview
export function navigateAfterIntake(
  navigate: NavigateFunction,
  motionId: string,
  locationState: any,
  llmFailed: boolean,
  onComplete?: (motionId: string) => void
): void {
  if (onComplete) {
    onComplete(motionId);
  }

  // If launched from FormExecution, navigate back to signal completion.
  // FormExecution is mounted at /case/forms — there is no /form/execution route.
  if (locationState?.fromFormExecution) {
    navigate('/case/forms', {
      state: {
        ...locationState,
        completedFormIndex: locationState.formExecutionFormIndex,
      },
    });
    return;
  }

  navigate(`/motion/${motionId}/preview`, { state: { llmFailed } });
}
