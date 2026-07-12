/**
 * Tests for legal page routes and rendering
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PrivacyPolicy } from '../legal/PrivacyPolicy';
import { Terms } from '../legal/Terms';

describe('PrivacyPolicy', () => {
  test('renders Privacy Policy heading', () => {
    render(<PrivacyPolicy />);
    expect(screen.getByRole('heading', { name: /privacy policy/i })).toBeInTheDocument();
  });

  test('renders Gmail section explaining user control', () => {
    render(<PrivacyPolicy />);
    expect(screen.getByText(/connecting gmail is optional/i)).toBeInTheDocument();
  });

  test('renders Google API Services link for Limited Use policy', () => {
    render(<PrivacyPolicy />);
    expect(screen.getByRole('link', { name: /google api services user data policy/i })).toBeInTheDocument();
  });
});

describe('Terms', () => {
  test('renders Terms of Service heading', () => {
    render(<Terms />);
    expect(screen.getByRole('heading', { name: /terms of service/i })).toBeInTheDocument();
  });

  test('renders the UPL disclaimer', () => {
    render(<Terms />);
    expect(screen.getByText(/not legal advice/i)).toBeInTheDocument();
  });
});
