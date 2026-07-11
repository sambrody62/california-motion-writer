import { useState, useEffect } from 'react';
import { profileAPI } from '../../services/api';
import { ServedMotionExtracted } from '../../services/servedMotionApi';
import { Question } from './QuestionField';

// Fields that can be auto-filled from user profile
const PROFILE_FIELD_MAP: Record<string, string> = {
  party_name: 'party_name',
  other_party_name: 'other_party_name',
  case_number: 'case_number',
  county: 'county',
  children_info: 'children_info',
};

// Wizard fields the served-motion upload may pre-fill. date_served is
// deliberately absent — it's when the user was served, not in the document,
// and the response deadline depends on the user entering it themselves.
const SERVED_MOTION_FIELDS = [
  'case_number',
  'petitioner_name',
  'hearing_date',
  'hearing_time',
  'other_party_requests',
] as const;

interface StepWithQuestions {
  questions: Question[];
}

interface UseIntakePrefillArgs {
  stepData: StepWithQuestions | null;
  getValues: (name: string) => any;
  setValue: (name: string, value: any, options?: any) => void;
}

// Owns profile autofill and served-motion prefill (upload wins over profile)
export const useIntakePrefill = ({ stepData, getValues, setValue }: UseIntakePrefillArgs) => {
  const [profile, setProfile] = useState<any>(null);
  const [prefilledFields, setPrefilledFields] = useState<Set<string>>(new Set());
  const [uploadPrefill, setUploadPrefill] = useState<ServedMotionExtracted | null>(null);
  const [uploadNotice, setUploadNotice] = useState<string | null>(null);
  const [uploadPrefilledFields, setUploadPrefilledFields] = useState<Set<string>>(new Set());

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const data = await profileAPI.getProfile();
        setProfile(data);
      } catch {
        // No profile — autofill skipped silently
      }
    };
    loadProfile();
  }, []);

  // Apply profile autofill whenever profile and stepData are both loaded
  useEffect(() => {
    if (profile && stepData) {
      applyProfileAutofill();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile, stepData]);

  // Apply served-motion prefill whenever a step loads (upload wins over profile)
  useEffect(() => {
    if (uploadPrefill && stepData) {
      applyUploadPrefill();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uploadPrefill, stepData]);

  const applyProfileAutofill = () => {
    if (!profile || !stepData) return;
    const newPrefilled = new Set<string>();

    stepData.questions.forEach((question) => {
      // Upload prefill owns these fields — the served motion is the better source
      if (uploadPrefill && question.id in uploadPrefill) return;
      const profileKey = PROFILE_FIELD_MAP[question.id];
      if (!profileKey) return;
      const profileValue = profile[profileKey];
      if (!profileValue) return;

      // Only fill if the field is currently empty
      const currentValue = getValues(question.id);
      if (!currentValue) {
        setValue(question.id, profileValue, { shouldValidate: false });
        newPrefilled.add(question.id);
      }
    });

    // Unconditional — stale badges from a previous step must always clear
    setPrefilledFields(newPrefilled);
  };

  const applyUploadPrefill = () => {
    if (!uploadPrefill || !stepData) return;
    const newPrefilled = new Set(uploadPrefilledFields);

    stepData.questions.forEach((question) => {
      const value = uploadPrefill[question.id as keyof ServedMotionExtracted];
      if (typeof value !== 'string' || !value) return;
      if (!getValues(question.id)) {
        setValue(question.id, value, { shouldValidate: false });
        newPrefilled.add(question.id);
      }
    });

    if (newPrefilled.size !== uploadPrefilledFields.size) {
      setUploadPrefilledFields(newPrefilled);
    }
  };

  const acceptUploadExtracted = (
    extracted: ServedMotionExtracted,
    notice: string | null
  ) => {
    const allowed: ServedMotionExtracted = {};
    SERVED_MOTION_FIELDS.forEach((key) => {
      const value = extracted[key];
      if (typeof value === 'string' && value) {
        allowed[key] = value;
      }
    });
    setUploadPrefill(Object.keys(allowed).length > 0 ? allowed : null);
    setUploadNotice(notice);
  };

  return {
    prefilledFields,
    uploadPrefill,
    uploadNotice,
    uploadPrefilledFields,
    acceptUploadExtracted,
  };
};
