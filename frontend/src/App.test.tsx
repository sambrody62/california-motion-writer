import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock the FirebaseAuthContext to avoid Firebase initialization issues in tests
jest.mock('./contexts/FirebaseAuthContext', () => ({
  FirebaseAuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useFirebaseAuth: () => ({
    user: null,
    loading: false,
    signIn: jest.fn(),
    signUp: jest.fn(),
    signOut: jest.fn(),
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

test('renders California Motion Writer app', () => {
  render(<App />);
  // Check for text that appears on the login page (login is shown when user is unauthenticated)
  const titleElement = screen.getByText(/Sign in to your account/i);
  expect(titleElement).toBeInTheDocument();
});
