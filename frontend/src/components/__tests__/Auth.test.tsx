import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import { Login } from '../auth/Login';
import { Register } from '../auth/Register';
import { PrivateRoute } from '../PrivateRoute';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const mockLogin = jest.fn();
const mockRegister = jest.fn();
const mockLogout = jest.fn();
let mockCurrentUser: { id: string; email: string } | null = null;

jest.mock('../../services/auth/auth.service', () => ({
  authService: {
    login: (...args: unknown[]) => mockLogin(...args),
    register: (...args: unknown[]) => mockRegister(...args),
    logout: (...args: unknown[]) => mockLogout(...args),
    onAuthStateChanged: (cb: (user: unknown) => void) => {
      cb(mockCurrentUser);
      return () => {};
    },
  },
}));

const renderWithAuth = (ui: React.ReactElement) =>
  render(
    <AuthProvider>
      <BrowserRouter>{ui}</BrowserRouter>
    </AuthProvider>
  );

beforeEach(() => {
  mockCurrentUser = null;
});

describe('Login', () => {
  it('logs in via the backend auth service and navigates to the dashboard', async () => {
    mockLogin.mockResolvedValue({ success: true, user: { id: 'u1', email: 'a@b.com' } });
    renderWithAuth(<Login />);

    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'secret123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('a@b.com', 'secret123'));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/dashboard'));
  });

  it('shows the error and stays put when login fails', async () => {
    mockLogin.mockResolvedValue({ success: false, error: 'Invalid credentials' });
    renderWithAuth(<Login />);

    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrongpass' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});

describe('Register', () => {
  it('registers via the backend auth service and navigates to profile setup', async () => {
    mockRegister.mockResolvedValue({ success: true, user: { id: 'u1', email: 'a@b.com' } });
    renderWithAuth(<Register />);

    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Password1' } });
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'Password1' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => expect(mockRegister).toHaveBeenCalledWith('a@b.com', 'Password1'));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/profile/setup'));
  });

  it('shows the error when registration fails', async () => {
    mockRegister.mockResolvedValue({ success: false, error: 'Email already registered' });
    renderWithAuth(<Register />);

    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Password1' } });
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'Password1' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Email already registered')).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});

describe('PrivateRoute', () => {
  const renderPrivate = () => {
    window.history.pushState({}, '', '/private');
    return render(
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route
              path="/private"
              element={
                <PrivateRoute>
                  <div>Secret content</div>
                </PrivateRoute>
              }
            />
            <Route path="/login" element={<div>Login page</div>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    );
  };

  it('redirects to login when no user is authenticated', () => {
    mockCurrentUser = null;
    renderPrivate();
    expect(screen.getByText('Login page')).toBeInTheDocument();
    expect(screen.queryByText('Secret content')).toBeNull();
  });

  it('renders children when a user is authenticated', () => {
    mockCurrentUser = { id: 'u1', email: 'a@b.com' };
    renderPrivate();
    expect(screen.getByText('Secret content')).toBeInTheDocument();
  });
});
