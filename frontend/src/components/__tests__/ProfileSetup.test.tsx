/**
 * ProfileSetup must not dump profile PII (children's names, addresses)
 * to the browser console.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const mockProfileGet = jest.fn();
const mockProfileCreate = jest.fn();
const mockProfileUpdate = jest.fn();

jest.mock('../../services/api', () => ({
  profileAPI: {
    get: (...args: any[]) => mockProfileGet(...args),
    create: (...args: any[]) => mockProfileCreate(...args),
    update: (...args: any[]) => mockProfileUpdate(...args),
  },
}));

import { ProfileSetup } from '../profile/ProfileSetup';

const PROFILE_WITH_CHILDREN = {
  case_number: 'FL-2024-001',
  county: 'San Diego',
  is_petitioner: true,
  party_name: 'Jane Doe',
  party_address: '123 Private Lane',
  party_phone: '555-0100',
  other_party_name: 'John Doe',
  children_info: [{ name: 'Johnny Secret', date_of_birth: '2018-01-01' }],
};

const renderPage = () => render(<BrowserRouter><ProfileSetup /></BrowserRouter>);

describe('ProfileSetup logging hygiene', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('does not log profile contents to the console on load', async () => {
    mockProfileGet.mockResolvedValue(PROFILE_WITH_CHILDREN);
    const logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue('Jane Doe')).toBeInTheDocument();
    });

    const loggedText = logSpy.mock.calls
      .map((call) => call.map((arg) => `${String(arg)} ${JSON.stringify(arg) ?? ''}`).join(' '))
      .join(' ');
    expect(loggedText).not.toContain('Johnny Secret');
    expect(loggedText).not.toContain('123 Private Lane');

    logSpy.mockRestore();
  });

  test('does not log the error object when no profile exists', async () => {
    mockProfileGet.mockRejectedValue(new Error('404 profile body with PII'));
    const logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

    renderPage();
    await waitFor(() => {
      expect(mockProfileGet).toHaveBeenCalled();
    });

    const loggedText = logSpy.mock.calls
      .map((call) => call.map((arg) => `${String(arg)} ${JSON.stringify(arg) ?? ''}`).join(' '))
      .join(' ');
    expect(loggedText).not.toContain('PII');

    logSpy.mockRestore();
  });
});
