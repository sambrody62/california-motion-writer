import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { EmergencyHelp } from '../emergency/EmergencyHelp';

// react-router-dom is globally mocked via moduleNameMapper in package.json.
// BrowserRouter from the mock wraps children in a plain <div>.

function renderWithRouter(component: React.ReactElement) {
  return render(<BrowserRouter>{component}</BrowserRouter>);
}

describe('EmergencyHelp', () => {
  beforeEach(() => {
    // Reset window.location.replace mock between tests
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { replace: jest.fn(), href: 'http://localhost/' },
    });
  });

  test('renders without authentication', () => {
    renderWithRouter(<EmergencyHelp />);
    expect(screen.getByText(/Emergency Legal Help/i)).toBeInTheDocument();
  });

  test('displays 911 danger banner', () => {
    renderWithRouter(<EmergencyHelp />);
    expect(
      screen.getByRole('alert')
    ).toHaveTextContent('If you are in danger right now, call 911.');
  });

  test('quick exit button is present', () => {
    renderWithRouter(<EmergencyHelp />);
    const btn = screen.getByRole('button', { name: /quick exit/i });
    expect(btn).toBeInTheDocument();
  });

  test('quick exit button calls window.location.replace with google.com', () => {
    renderWithRouter(<EmergencyHelp />);
    const btn = screen.getByRole('button', { name: /quick exit/i });
    fireEvent.click(btn);
    expect(window.location.replace).toHaveBeenCalledWith('https://www.google.com');
  });

  test('shows DVRO option card heading', () => {
    renderWithRouter(<EmergencyHelp />);
    const heading = screen.getByRole('heading', { name: /Domestic Violence Restraining Order/i });
    expect(heading).toBeInTheDocument();
  });

  test('shows emergency custody option card heading', () => {
    renderWithRouter(<EmergencyHelp />);
    const heading = screen.getByRole('heading', { name: /Emergency.*Custody Order/i });
    expect(heading).toBeInTheDocument();
  });

  test('shows National DV Hotline number', () => {
    renderWithRouter(<EmergencyHelp />);
    expect(screen.getByText(/1-800-799-7233/)).toBeInTheDocument();
  });

  test('shows text hotline instruction', () => {
    renderWithRouter(<EmergencyHelp />);
    expect(screen.getByText(/88788/)).toBeInTheDocument();
  });

  test('DVRO links go to self-help courts site', () => {
    renderWithRouter(<EmergencyHelp />);
    const links = screen.getAllByRole('link');
    const dvroSelfHelp = links.find(
      (l) => l.getAttribute('href') === 'https://selfhelp.courts.ca.gov/DV-restraining-order'
    );
    expect(dvroSelfHelp).toBeDefined();
  });

  test('custody self-help link is present', () => {
    renderWithRouter(<EmergencyHelp />);
    const links = screen.getAllByRole('link');
    const custodyLink = links.find(
      (l) => l.getAttribute('href') === 'https://selfhelp.courts.ca.gov/child-custody'
    );
    expect(custodyLink).toBeDefined();
  });

  test('shelter finder link is present', () => {
    renderWithRouter(<EmergencyHelp />);
    const links = screen.getAllByRole('link');
    const shelterLink = links.find(
      (l) => l.getAttribute('href') === 'https://www.domesticshelters.org/'
    );
    expect(shelterLink).toBeDefined();
  });
});
