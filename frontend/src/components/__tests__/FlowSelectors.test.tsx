import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MotionFlowSelector } from '../motion/MotionFlowSelector';
import { FormFlowSelector } from '../forms/FormFlowSelector';

const mockNavigate = jest.fn();
let mockParams: Record<string, string> = {};

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => mockParams,
}));

beforeEach(() => {
  mockNavigate.mockClear();
});

describe('MotionFlowSelector', () => {
  beforeEach(() => {
    mockParams = { motionType: 'RFO' };
  });

  it('does not offer the chat flow', () => {
    render(<MotionFlowSelector />);
    expect(screen.queryByText(/Chat with Assistant/i)).toBeNull();
    expect(screen.queryByText(/Recommended for first-timers/i)).toBeNull();
  });

  it('still navigates to guided forms', () => {
    render(<MotionFlowSelector />);
    fireEvent.click(screen.getByRole('button', { name: /Guided Forms/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/motion/guided/RFO');
  });
});

describe('FormFlowSelector', () => {
  beforeEach(() => {
    mockParams = { formType: 'FL-300' };
  });

  it('does not offer the chat flow, even for complex forms', () => {
    render(<FormFlowSelector />);
    expect(screen.queryByText(/Chat with Assistant/i)).toBeNull();
    expect(screen.queryByText(/chat assistant/i)).toBeNull();
  });

  it('still navigates to guided forms', () => {
    render(<FormFlowSelector />);
    fireEvent.click(screen.getByRole('button', { name: /Guided Forms/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/form/guided/FL-300');
  });
});
