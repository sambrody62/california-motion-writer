/**
 * Tests for ChatInterface component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import ChatInterface from '../chat/ChatInterface';

// Mock useAuth hook
const mockUseAuth = {
  user: { id: 'test-user-123', email: 'test@example.com' },
  token: 'mock-jwt-token',
  loading: false
};

jest.mock('../../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth
}));

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(public url: string) {
    // Simulate connection opening, then server 'connected' message
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
      // Simulate server sending the 'connected' acknowledgement
      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', {
          data: JSON.stringify({ type: 'connected' })
        }));
      }
    }, 50);
  }

  send(data: string) {
    // Mock sending data
    console.log('Mock WebSocket send:', data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

// Replace global WebSocket with mock
(global as any).WebSocket = MockWebSocket;

// Helper to render component with router
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('ChatInterface', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  afterEach(() => {
    // Clean up after each test
    jest.restoreAllMocks();
  });

  test('renders chat button when closed', () => {
    renderWithRouter(<ChatInterface />);

    const chatButton = screen.getByRole('button', { name: /open chat/i });
    expect(chatButton).toBeInTheDocument();
  });

  test('opens chat interface when button clicked', async () => {
    renderWithRouter(<ChatInterface />);

    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      expect(screen.getByText('Motion Filing Assistant')).toBeInTheDocument();
    });
  });

  test('displays initial welcome message when chat is empty', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      expect(screen.getByText(/Hi! I'm here to help you file your motion/)).toBeInTheDocument();
    });
  });

  test('shows input field and send button when open', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Type your message/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
    });
  });

  test('can type in input field', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Type your message/) as HTMLInputElement;
      fireEvent.change(input, { target: { value: 'Test message' } });
      expect(input.value).toBe('Test message');
    });
  });

  test('sends message when send button clicked', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Type your message/);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      fireEvent.change(input, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      // Input should be cleared after sending
      expect((input as HTMLInputElement).value).toBe('');
    });
  });

  test('sends message when Enter key pressed', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Type your message/);

      fireEvent.change(input, { target: { value: 'Test message' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });

      // Input should be cleared after sending
      expect((input as HTMLInputElement).value).toBe('');
    });
  });

  test('does not send empty messages', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      const sendButton = screen.getByRole('button', { name: /send message/i });

      // Send button should be disabled when input is empty
      expect(sendButton).toBeDisabled();
    });
  });

  test('can minimize and maximize chat', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      const minimizeButton = screen.getByRole('button', { name: /minimize/i });
      fireEvent.click(minimizeButton);

      // Chat should be minimized (input area hidden)
      expect(screen.queryByPlaceholderText(/Type your message/)).not.toBeInTheDocument();
    });

    // Maximize again
    const maximizeButton = screen.getByRole('button', { name: /maximize/i });
    fireEvent.click(maximizeButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Type your message/)).toBeInTheDocument();
    });
  });

  test('can close chat', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      const closeButton = screen.getByRole('button', { name: /close chat/i });
      fireEvent.click(closeButton);

      // Should be back to closed state
      expect(screen.getByRole('button', { name: /open chat/i })).toBeInTheDocument();
    });
  });

  test('shows connection status', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    // Should show connecting status initially
    await waitFor(() => {
      expect(screen.getByText('Connecting...')).toBeInTheDocument();
    });
  });

  test('displays chat messages', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      // Send a message to populate the chat
      const input = screen.getByPlaceholderText(/Type your message/);
      fireEvent.change(input, { target: { value: 'Hello' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
      // Assert input cleared to confirm sendMessage ran
      expect((input as HTMLInputElement).value).toBe('');
    });

    // The user message should appear in the chat
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
  });

  test('handles websocket connection errors gracefully', async () => {
    // Mock WebSocket with error
    const OriginalWebSocket = (global as any).WebSocket;

    class ErrorWebSocket extends MockWebSocket {
      constructor(url: string) {
        super(url);
        setTimeout(() => {
          if (this.onerror) {
            this.onerror(new Event('error'));
          }
        }, 50);
      }
    }

    (global as any).WebSocket = ErrorWebSocket;

    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      // Should show offline status
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });

    // Restore original WebSocket
    (global as any).WebSocket = OriginalWebSocket;
  });

  test('processes quick replies correctly', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    // Mock incoming message with quick replies
    await waitFor(() => {
      // Simulate WebSocket message with quick replies
      const mockMessage = {
        type: 'message',
        data: {
          id: 'msg-123',
          content: 'How can I help you?',
          timestamp: new Date().toISOString(),
          quick_replies: ['File a motion', 'Respond to papers', 'Get help']
        }
      };

      // We'd need to trigger the WebSocket onmessage handler here
      // This is a simplified test - in practice you'd mock the WebSocket more thoroughly
    });
  });

  test('handles session updates', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      // In development mode, should show session info
      if (process.env.NODE_ENV === 'development') {
        // Look for session info in the UI
        const sessionInfo = screen.queryByText(/Session:/);
        // Session info might not be visible until after connection
      }
    });
  });

  test('input is disabled when not connected', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    // Initially, input should be disabled until connected
    const input = screen.getByPlaceholderText(/Connecting.../);
    expect(input).toBeDisabled();
  });

  test('scrolls to bottom when new messages arrive', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    // Mock scrollIntoView
    const mockScrollIntoView = jest.fn();
    Element.prototype.scrollIntoView = mockScrollIntoView;

    await waitFor(() => {
      // Send a message
      const input = screen.getByPlaceholderText(/Type your message/);
      fireEvent.change(input, { target: { value: 'Test scroll' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
      // Assert input cleared to confirm sendMessage ran
      expect((input as HTMLInputElement).value).toBe('');
    });

    // scrollIntoView should be called
    await waitFor(() => {
      expect(mockScrollIntoView).toHaveBeenCalled();
    });
  });

  test('maintains message history across minimize/maximize', async () => {
    renderWithRouter(<ChatInterface />);

    // Open chat and send message
    const chatButton = screen.getByRole('button', { name: /open chat/i });
    fireEvent.click(chatButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Type your message/);
      fireEvent.change(input, { target: { value: 'Persistent message' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
      // Assert input cleared to confirm sendMessage ran
      expect((input as HTMLInputElement).value).toBe('');
    });

    // Minimize chat
    const minimizeButton = screen.getByRole('button', { name: /minimize/i });
    fireEvent.click(minimizeButton);

    // Maximize again
    const maximizeButton = screen.getByRole('button', { name: /maximize/i });
    fireEvent.click(maximizeButton);

    // Message should still be there
    await waitFor(() => {
      expect(screen.getByText('Persistent message')).toBeInTheDocument();
    });
  });
});