import { useState, useEffect } from 'react';
import { motionAPI } from '../../services/api';
import { FormType } from '../../types/forms';

// A form counts as done once a motion of that type has finished LLM
// processing (ready_for_review) or was explicitly completed.
const COMPLETE_STATUSES = new Set(['ready_for_review', 'completed']);

interface MotionSummary {
  id: string;
  motion_type: string;
  status: string;
}

// Derives which recommended forms are already complete from server-side
// motion status — the in-memory Set alone lost completions across the
// guided-intake round trip (real-LLM browser finding L13). markComplete
// remains the location.state fast path for the return-from-intake signal.
export const useFormCompletion = (forms: FormType[]) => {
  const [completedForms, setCompletedForms] = useState<Set<number>>(new Set());

  useEffect(() => {
    let cancelled = false;
    const loadServerCompletion = async () => {
      try {
        const motions: MotionSummary[] = await motionAPI.list();
        const doneTypes = new Set(
          (motions || [])
            .filter((motion) => COMPLETE_STATUSES.has(motion.status))
            .map((motion) => motion.motion_type)
        );
        const doneIndexes = forms
          .map((form, index) => (doneTypes.has(form) ? index : -1))
          .filter((index) => index >= 0);
        if (!cancelled && doneIndexes.length > 0) {
          setCompletedForms((prev) => new Set(Array.from(prev).concat(doneIndexes)));
        }
      } catch {
        // Server state unavailable — the fast path still marks completions
      }
    };
    loadServerCompletion();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const markComplete = (index: number) => {
    setCompletedForms((prev) => new Set(Array.from(prev).concat(index)));
  };

  return { completedForms, markComplete };
};
