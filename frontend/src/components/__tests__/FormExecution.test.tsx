/**
 * Tests for FormExecution — the gameplan form-execution loop.
 * Form completion must derive from server-side motion status (real-LLM
 * browser finding L13: the FL-300 card never marked complete after the
 * guided loop), with the location.state return signal as a fast path.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { FormExecution } from '../case/FormExecution';

const mockNavigate = jest.fn();
let mockLocationState: any = null;

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: mockLocationState, pathname: '/case/forms' }),
}));

const mockListMotions = jest.fn();

jest.mock('../../services/api', () => ({
  motionAPI: {
    list: (...args: any[]) => mockListMotions(...args),
  },
}));

const GAMEPLAN = {
  analysis: 'Custody enforcement case',
  legalStrategy: 'File an FL-300 to enforce the existing order.',
  recommendedForms: ['FL-300', 'FL-410'],
  timeline: 'File within two weeks',
  keyConsiderations: ['Keep records'],
  nextSteps: ['Gather orders'],
};

const baseState = () => ({
  gameplan: { ...GAMEPLAN, recommendedForms: [...GAMEPLAN.recommendedForms] },
  caseDescription: 'Missed exchanges',
  sessionId: 'session-1',
});

const renderPage = () => render(<BrowserRouter><FormExecution /></BrowserRouter>);

const cardFor = (formId: string) =>
  screen.getByText(formId).closest('.rounded-lg') as HTMLElement;

// The card's completion indicator: the number circle turns into a green
// check (the border also greens, unless the card is the current one)
const isCardComplete = (formId: string) =>
  Boolean(cardFor(formId).querySelector('.bg-green-600'));

describe('FormExecution', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocationState = baseState();
    mockListMotions.mockResolvedValue([]);
  });

  test('redirects to case intake when no gameplan state is present', async () => {
    mockLocationState = null;
    renderPage();

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/case/intake'));
  });

  test('renders a card for every recommended form', async () => {
    renderPage();

    expect(await screen.findByText('Request for Order')).toBeInTheDocument();
    expect(screen.getByText('Order to Show Cause for Contempt')).toBeInTheDocument();
  });

  test('marks a form complete from server-side motion status', async () => {
    // Bare array — motionAPI.list returns the unwrapped response body
    mockListMotions.mockResolvedValue([
      { id: 'motion-1', motion_type: 'FL-300', status: 'ready_for_review' },
    ]);

    renderPage();

    await waitFor(() => {
      expect(isCardComplete('FL-300')).toBe(true);
    });
    expect(isCardComplete('FL-410')).toBe(false);
  });

  test('draft motions do not mark a form complete', async () => {
    mockListMotions.mockResolvedValue([
      { id: 'motion-1', motion_type: 'FL-300', status: 'draft' },
    ]);

    renderPage();

    await screen.findByText('Request for Order');
    expect(isCardComplete('FL-300')).toBe(false);
  });

  test('location.state fast path marks the returned form complete', async () => {
    mockLocationState = { ...baseState(), completedFormIndex: 0 };

    renderPage();

    await waitFor(() => {
      expect(isCardComplete('FL-300')).toBe(true);
    });
  });

  test('shows the all-complete screen when every form has a completed motion', async () => {
    mockLocationState = {
      ...baseState(),
      gameplan: { ...GAMEPLAN, recommendedForms: ['FL-300'] },
    };
    mockListMotions.mockResolvedValue([
      { id: 'motion-1', motion_type: 'FL-300', status: 'completed' },
    ]);

    renderPage();

    expect(await screen.findByText(/All Forms Completed/i)).toBeInTheDocument();
  });
});
