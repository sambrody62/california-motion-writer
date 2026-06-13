export type EvidenceType = 'text' | 'email' | 'photo' | 'document';

export type EvidenceTag =
  | 'threat'
  | 'non_payment'
  | 'custody_violation'
  | 'promise_to_follow'
  | 'false_claim'
  | 'other';

export interface Evidence {
  id: string;
  evidence_type: EvidenceType;
  tags: EvidenceTag[];
  source_date: string | null;
  description: string;
  transcription: string | null;
  filename: string | null;
  user_confirmed?: boolean;
}

export const TAG_LABELS: Record<EvidenceTag, string> = {
  threat: 'Threat',
  non_payment: 'Missed payment',
  custody_violation: 'Custody violation',
  promise_to_follow: 'Promise to follow order',
  false_claim: 'False claim',
  other: 'Other',
};

export const ALL_TAGS: EvidenceTag[] = [
  'threat',
  'non_payment',
  'custody_violation',
  'promise_to_follow',
  'false_claim',
  'other',
];
