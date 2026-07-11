import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motionAPI } from '../../services/api';

interface MotionDraft {
  step_number: number;
  question_data: Record<string, unknown>;
}

export interface MotionInit {
  motionId: string | null;
  currentFormType: string | undefined;
  initialStep: number;
  resumeAnswers: Record<string, unknown>;
  isResume: boolean;
}

// /motion/new/response and /motion/new/rfo are route aliases with no form
// template of their own — unnormalized they created motions the wizard could
// never load a step for (L16). Applied before BOTH motion creation and
// template lookup.
const normalizeFormType = (raw: string | undefined): string | undefined => {
  const lowered = raw?.toLowerCase();
  if (lowered === 'response') return 'FL-320';
  if (lowered === 'rfo') return 'FL-300';
  return raw;
};

// Create a new draft motion (/form/guided/:formType, /motion/guided/:motionType)
// or load an existing one (/motion/:motionId/edit/:stepNumber) — never both.
export const useMotionInit = (): MotionInit => {
  const { motionType, formType, motionId: motionIdParam, stepNumber } = useParams<{
    motionType?: string;
    formType?: string;
    motionId?: string;
    stepNumber?: string;
  }>();
  const navigate = useNavigate();

  const isResume = Boolean(motionIdParam);
  const createFormType = normalizeFormType(formType || motionType);

  const [motionId, setMotionId] = useState<string | null>(null);
  const [currentFormType, setCurrentFormType] = useState<string | undefined>(
    isResume ? undefined : createFormType
  );
  const [resumeAnswers, setResumeAnswers] = useState<Record<string, unknown>>({});
  const initialStep = isResume ? parseInt(stepNumber || '1', 10) || 1 : 1;
  // One init per entry — StrictMode double-fires this effect in dev, which
  // created a paired POST /motions/ and an orphan draft per visit (L11)
  const initKeyRef = useRef<string | null>(null);

  useEffect(() => {
    const loadExistingMotion = async () => {
      try {
        const motion = await motionAPI.get(motionIdParam!);
        // Merge every saved step's answers so conditional questions on later
        // steps still see the context entered on earlier ones
        const merged: Record<string, unknown> = {};
        ([...(motion.drafts || [])] as MotionDraft[])
          .sort((a, b) => a.step_number - b.step_number)
          .forEach((draft) => Object.assign(merged, draft.question_data || {}));
        setResumeAnswers(merged);
        setCurrentFormType(motion.motion_type);
        setMotionId(motion.id);
      } catch (error) {
        console.error('Failed to load motion:', error);
        navigate('/dashboard');
      }
    };

    const createMotion = async () => {
      try {
        const response = await motionAPI.create({
          motion_type: createFormType,
          status: 'draft',
        });
        const id = response?.data?.id || response?.id;
        setMotionId(id);
      } catch (error) {
        console.error('Failed to create motion:', error);
        navigate('/dashboard');
      }
    };

    const initKey = motionIdParam ?? `create:${createFormType}`;
    if (initKeyRef.current === initKey) return;
    initKeyRef.current = initKey;

    if (motionIdParam) {
      loadExistingMotion();
    } else {
      createMotion();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [motionIdParam, createFormType]);

  return { motionId, currentFormType, initialStep, resumeAnswers, isResume };
};
