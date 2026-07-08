import api from './api';

export interface BatchPerFile {
  filename: string;
  ok: boolean;
  chars: number;
}

export interface BatchUploadResult {
  merged_transcript: string;
  participants: string[];
  date_range: { start: string | null; end: string | null };
  suggested_source_date: string | null;
  per_file: BatchPerFile[];
  notice: string | null;
}

export const evidenceBatchAPI = {
  // Returns the unwrapped response body (lessons.md — helpers never return
  // the axios response itself). Analysis only; nothing is persisted.
  batchUpload: async (motionId: string, files: File[]): Promise<BatchUploadResult> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const response = await api.post(
      `/motions/${motionId}/evidence/batch-upload`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },
};
