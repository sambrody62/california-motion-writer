/**
 * Tests for evidence deletion — must require confirmation and surface errors
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ motionId: 'motion-abc' }),
}));

const mockEvidenceList = jest.fn();
const mockEvidenceCreate = jest.fn();
const mockEvidenceUpload = jest.fn();
const mockEvidenceRemove = jest.fn();

jest.mock('../../services/api', () => ({
  evidenceAPI: {
    list: (...args: any[]) => mockEvidenceList(...args),
    create: (...args: any[]) => mockEvidenceCreate(...args),
    upload: (...args: any[]) => mockEvidenceUpload(...args),
    remove: (...args: any[]) => mockEvidenceRemove(...args),
  },
}));

import { EvidenceManager } from '../evidence/EvidenceManager';

const sampleEvidence = [
  {
    id: 'ev-1',
    evidence_type: 'text' as const,
    tags: ['threat'],
    source_date: '2024-03-01',
    description: 'Text threatening custody',
    transcription: 'I will take the kids away',
    filename: null,
  },
];

const renderManager = () =>
  render(
    <BrowserRouter>
      <EvidenceManager />
    </BrowserRouter>
  );

describe('Evidence deletion', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockEvidenceList.mockResolvedValue(sampleEvidence);
    mockEvidenceRemove.mockResolvedValue({ success: true });
  });

  test('clicking the trash icon asks for confirmation instead of deleting', async () => {
    renderManager();
    await screen.findByText('Text threatening custody');

    fireEvent.click(screen.getByRole('button', { name: /remove evidence/i }));

    expect(mockEvidenceRemove).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: /confirm delete/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  test('confirming deletes the item', async () => {
    renderManager();
    await screen.findByText('Text threatening custody');

    fireEvent.click(screen.getByRole('button', { name: /remove evidence/i }));
    fireEvent.click(screen.getByRole('button', { name: /confirm delete/i }));

    await waitFor(() => expect(mockEvidenceRemove).toHaveBeenCalledWith('ev-1'));
    await waitFor(() =>
      expect(screen.queryByText('Text threatening custody')).not.toBeInTheDocument()
    );
  });

  test('cancelling keeps the item and never calls the API', async () => {
    renderManager();
    await screen.findByText('Text threatening custody');

    fireEvent.click(screen.getByRole('button', { name: /remove evidence/i }));
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

    expect(mockEvidenceRemove).not.toHaveBeenCalled();
    expect(screen.getByText('Text threatening custody')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /confirm delete/i })).not.toBeInTheDocument();
  });

  test('a failed delete shows an error and keeps the item in the list', async () => {
    mockEvidenceRemove.mockRejectedValue(new Error('network down'));
    renderManager();
    await screen.findByText('Text threatening custody');

    fireEvent.click(screen.getByRole('button', { name: /remove evidence/i }));
    fireEvent.click(screen.getByRole('button', { name: /confirm delete/i }));

    expect(await screen.findByText(/couldn't delete/i)).toBeInTheDocument();
    expect(screen.getByText('Text threatening custody')).toBeInTheDocument();
  });
});
