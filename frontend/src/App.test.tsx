import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { EmergencyHelp } from './components/emergency/EmergencyHelp';
import { BrowserRouter } from 'react-router-dom';

// Mock the AuthContext so tests don't hit the backend auth service
jest.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    loading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
  })
}));

// HashRouter was removed in react-router-dom v7; provide it as an alias for BrowserRouter
jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');
  return {
    ...actual,
    HashRouter: actual.BrowserRouter,
  };
});

// Silence console.error noise from components mounting with missing data
beforeEach(() => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => {
  jest.restoreAllMocks();
});

test('renders California Motion Writer app', () => {
  render(<App />);
  // Check for text that appears on the login page (login is shown when user is unauthenticated)
  const titleElement = screen.getByText(/Sign in to your account/i);
  expect(titleElement).toBeInTheDocument();
});

// EmergencyHelp is a public component — test it directly to verify
// it renders without any authentication context.

test('/emergency route renders without authentication', () => {
  render(<BrowserRouter><EmergencyHelp /></BrowserRouter>);
  expect(screen.getByText(/If you are in danger right now, call 911/i)).toBeInTheDocument();
});

test('/emergency route has quick exit button', () => {
  render(<BrowserRouter><EmergencyHelp /></BrowserRouter>);
  expect(screen.getByRole('button', { name: /quick exit/i })).toBeInTheDocument();
});

test('/emergency route has 911 banner', () => {
  render(<BrowserRouter><EmergencyHelp /></BrowserRouter>);
  expect(screen.getByRole('alert')).toBeInTheDocument();
});
