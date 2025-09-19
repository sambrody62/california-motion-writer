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

test('renders California Motion Writer app', () => {
  render(<App />);
  // Check for the app title that appears on the login page
  const titleElement = screen.getByText(/California Motion Writer/i);
  expect(titleElement).toBeInTheDocument();
});
