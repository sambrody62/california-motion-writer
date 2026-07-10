/**
 * Tests for CaseIntake — UPL-safe copy (finding F6: user-facing text must say
 * "action plan", never "legal strategy").
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { CaseIntake } from '../case/CaseIntake';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const renderPage = () => render(<BrowserRouter><CaseIntake /></BrowserRouter>);

describe('CaseIntake', () => {
  it('renders without UPL-risky "legal strategy" copy', () => {
    renderPage();

    expect(screen.queryByText(/legal strategy/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /action plan/i })).toBeInTheDocument();
  });

  it('keeps copy UPL-safe when the existing-gameplan option is selected', () => {
    renderPage();

    fireEvent.click(screen.getByText(/I have an existing gameplan/i));

    expect(screen.queryByText(/legal strategy/i)).not.toBeInTheDocument();
    expect(
      screen.queryByPlaceholderText(/legal strategy/i)
    ).not.toBeInTheDocument();
  });
});
