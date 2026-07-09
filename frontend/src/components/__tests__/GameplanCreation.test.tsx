/**
 * Tests for GameplanCreation — honest fallback when the LLM output can't be parsed
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { GameplanCreation } from '../case/GameplanCreation';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({
    state: { caseDescription: 'Custody schedule dispute with missed exchanges' },
    pathname: '/case/gameplan',
  }),
}));

const mockCreateSession = jest.fn();
const mockSendMessage = jest.fn();

jest.mock('../../services/api', () => ({
  chat: {
    createSession: (...args: any[]) => mockCreateSession(...args),
    sendMessage: (...args: any[]) => mockSendMessage(...args),
  },
}));

const RICH_RESPONSE = `
1. Case Analysis
Your situation involves a custody schedule dispute that the court can address.

2. Legal Strategy
File an FL-300 requesting a modified visitation schedule.

3. Next Steps
1. Gather your existing court orders
2. Complete the FL-300
`;

const renderPage = () => render(<BrowserRouter><GameplanCreation /></BrowserRouter>);

describe('GameplanCreation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateSession.mockResolvedValue({ session_id: 'session-1' });
  });

  test('shows the personalized plan without a fallback notice when parsing succeeds', async () => {
    mockSendMessage.mockResolvedValue(RICH_RESPONSE);
    renderPage();

    expect(await screen.findByText('Case Analysis')).toBeInTheDocument();
    expect(screen.queryByText(/couldn't generate a personalized plan/i)).toBeNull();
  });

  test('shows an honest fallback state when the LLM output is unparseable', async () => {
    mockSendMessage.mockResolvedValue('OK');
    renderPage();

    expect(
      await screen.findByText(/couldn't generate a personalized plan/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/not tailored to your case/i)).toBeInTheDocument();
  });
});
