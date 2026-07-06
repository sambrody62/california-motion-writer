/**
 * Tests for Dashboard component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { Dashboard } from '../Dashboard';

// Mock the Firebase Auth context
const mockFirebaseAuth = {
  user: {
    email: 'test@example.com',
    uid: 'test-uid'
  },
  logout: jest.fn()
};

jest.mock('../../contexts/FirebaseAuthContext', () => ({
  useFirebaseAuth: () => mockFirebaseAuth
}));

// Mock the API services
jest.mock('../../services/api', () => ({
  motionAPI: {
    list: jest.fn()
  },
  profileAPI: {
    get: jest.fn()
  }
}));

// Mock react-router-dom navigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

// Mock date-fns format function
jest.mock('date-fns', () => ({
  format: (date: Date, formatStr: string) => {
    if (formatStr === 'MMM d, yyyy') return 'Jan 1, 2024';
    if (formatStr === 'MMM d, yyyy h:mm a') return 'Jan 1, 2024 9:00 AM';
    return date.toString();
  }
}));

// Helper to render component with router
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

// Get the mocked API services
const { motionAPI, profileAPI } = jest.requireMock('../../services/api');

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset API mocks
    motionAPI.list.mockResolvedValue([]);
    profileAPI.get.mockRejectedValue(new Error('No profile found'));
  });

  test('renders dashboard header with user email', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('California Motion Writer')).toBeInTheDocument();
      expect(screen.getByText('Welcome back, test@example.com')).toBeInTheDocument();
    });
  });

  test('shows profile setup notice when no profile exists', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Complete your profile first/)).toBeInTheDocument();
      expect(screen.getByText(/Set up profile →/)).toBeInTheDocument();
    });
  });

  test('hides profile setup notice when profile exists', async () => {
    profileAPI.get.mockResolvedValue({
      id: 'profile-123',
      party_name: 'John Doe',
      case_number: 'FL-2024-001'
    });

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.queryByText(/Complete your profile first/)).not.toBeInTheDocument();
    });
  });

  test('displays start new case button prominently', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      const startButton = screen.getByRole('button', { name: /Start Your Case/i });
      expect(startButton).toBeInTheDocument();
    });
  });

  test('navigates to profile setup when no profile and start case clicked', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      const startButton = screen.getByRole('button', { name: /Start Your Case/i });
      fireEvent.click(startButton);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/profile/setup');
  });

  test('navigates to case intake when profile exists and start case clicked', async () => {
    // Override the default profile rejection for this test
    profileAPI.get.mockResolvedValueOnce({
      id: 'profile-123',
      party_name: 'John Doe'
    });

    renderWithRouter(<Dashboard />);

    // Wait for loading to complete first
    await waitFor(() => {
      expect(screen.queryByRole('status', { hidden: true })).not.toBeInTheDocument();
    });

    // Now click the main start button (first one)
    const startButtons = screen.getAllByRole('button', { name: /Start Your Case/i });
    fireEvent.click(startButtons[0]);

    expect(mockNavigate).toHaveBeenCalledWith('/case/intake');
  });

  test('displays how it works section', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('How It Works')).toBeInTheDocument();
      expect(screen.getByText('Explain Your Case')).toBeInTheDocument();
      expect(screen.getByText('Get Your Strategy')).toBeInTheDocument();
      expect(screen.getByText('File Your Forms')).toBeInTheDocument();
    });
  });

  test('shows empty state when no motions exist', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('No motions')).toBeInTheDocument();
      expect(screen.getByText('Get started by creating a new motion.')).toBeInTheDocument();
    });
  });

  test('displays motions list when motions exist', async () => {
    const mockMotions = [
      {
        id: 'motion-1',
        motion_type: 'RFO',
        case_caption: 'Smith v. Smith',
        case_number: 'FL-2024-001',
        status: 'draft',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T11:00:00Z',
        hearing_date: '2024-02-01',
        hearing_time: '09:00'
      },
      {
        id: 'motion-2',
        motion_type: 'RESPONSE',
        case_caption: 'Johnson v. Johnson',
        case_number: 'FL-2024-002',
        status: 'complete',
        created_at: '2024-01-02T10:00:00Z',
        updated_at: '2024-01-02T11:00:00Z'
      }
    ];

    motionAPI.list.mockResolvedValue(mockMotions);

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Smith v. Smith')).toBeInTheDocument();
      expect(screen.getByText('Johnson v. Johnson')).toBeInTheDocument();
      expect(screen.getByText('Case #: FL-2024-001')).toBeInTheDocument();
      expect(screen.getByText('Case #: FL-2024-002')).toBeInTheDocument();
    });
  });

  test('displays motion status badges correctly', async () => {
    const mockMotions = [
      {
        id: 'motion-1',
        motion_type: 'RFO',
        case_caption: 'Test Motion',
        status: 'draft',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T11:00:00Z'
      }
    ];

    motionAPI.list.mockResolvedValue(mockMotions);

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('draft')).toBeInTheDocument();
    });
  });

  test('shows hearing dates when available', async () => {
    const mockMotions = [
      {
        id: 'motion-1',
        motion_type: 'RFO',
        case_caption: 'Motion with Hearing',
        status: 'filed',
        hearing_date: '2024-02-15',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T11:00:00Z'
      }
    ];

    motionAPI.list.mockResolvedValue(mockMotions);

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Hearing: Jan 1, 2024/)).toBeInTheDocument();
    });
  });

  test('navigation to profile page works', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      // Get the header profile button specifically (has SVG icon)
      const profileButtons = screen.getAllByRole('button', { name: /Profile/i });
      const headerProfileButton = profileButtons.find(button =>
        button.querySelector('svg') !== null
      );
      fireEvent.click(headerProfileButton!);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/profile/setup');
  });

  test('sign out functionality works', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      const signOutButton = screen.getByRole('button', { name: /Sign Out/i });
      fireEvent.click(signOutButton);
    });

    expect(mockFirebaseAuth.logout).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  test('motion click navigation works', async () => {
    const mockMotions = [
      {
        id: 'motion-123',
        motion_type: 'RFO',
        case_caption: 'Clickable Motion',
        status: 'draft',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T11:00:00Z'
      }
    ];

    motionAPI.list.mockResolvedValue(mockMotions);

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      const motionLink = screen.getByText('Clickable Motion');
      fireEvent.click(motionLink);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/motion/motion-123');
  });

  test('handles API errors gracefully', async () => {
    motionAPI.list.mockRejectedValue(new Error('API Error'));

    // Mock console.error to avoid noise in test output
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      // Should still render the page even with API errors
      expect(screen.getByText('California Motion Writer')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  test('shows loading state initially', () => {
    renderWithRouter(<Dashboard />);

    // Should show loading spinner initially
    const spinnerElement = document.querySelector('.animate-spin');
    expect(spinnerElement).toBeInTheDocument();
  });

  test('handles empty motion list correctly', async () => {
    motionAPI.list.mockResolvedValue([]);

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('No motions')).toBeInTheDocument();
    });
  });

  test('displays last updated times correctly', async () => {
    const mockMotions = [
      {
        id: 'motion-1',
        motion_type: 'RFO',
        case_caption: 'Recent Motion',
        status: 'draft',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T11:00:00Z'
      }
    ];

    motionAPI.list.mockResolvedValue(mockMotions);

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated: Jan 1, 2024 9:00 AM/)).toBeInTheDocument();
    });
  });

  test('handles motion with missing case number', async () => {
    const mockMotions = [
      {
        id: 'motion-1',
        motion_type: 'RFO',
        case_caption: 'Motion Without Case Number',
        case_number: null,
        status: 'draft',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T11:00:00Z'
      }
    ];

    motionAPI.list.mockResolvedValue(mockMotions);

    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Case #: Draft')).toBeInTheDocument();
    });
  });

  test('start case button appears in empty state', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      // Should have multiple "Start Your Case" buttons - one in hero and one in empty state
      const startButtons = screen.getAllByText('Start Your Case');
      expect(startButtons.length).toBeGreaterThan(0);
    });
  });

  test('displays emergency protection link to /emergency', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      const emergencyLink = screen.getByRole('link', { name: /Need emergency protection\?/i });
      expect(emergencyLink).toBeInTheDocument();
      expect(emergencyLink).toHaveAttribute('href', '/emergency');
    });
  });

  test('displays enforce existing order card', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Enforce an existing order/i)).toBeInTheDocument();
    });
  });

  test('enforce existing order card links to /violation/intake', async () => {
    renderWithRouter(<Dashboard />);

    await waitFor(() => {
      const enforceButton = screen.getByRole('button', { name: /Enforce an existing order/i });
      fireEvent.click(enforceButton);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/violation/intake');
  });
});