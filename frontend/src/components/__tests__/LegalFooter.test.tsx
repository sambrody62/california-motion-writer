import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { LegalFooter } from '../legal/LegalFooter';

describe('LegalFooter', () => {
  const renderFooter = () => render(<BrowserRouter><LegalFooter /></BrowserRouter>);

  it('links to the terms and privacy pages', () => {
    renderFooter();
    expect(screen.getByRole('link', { name: /terms/i })).toHaveAttribute('href', '/terms');
    expect(screen.getByRole('link', { name: /privacy/i })).toHaveAttribute('href', '/privacy');
  });

  it('states that the product is not legal advice', () => {
    renderFooter();
    expect(screen.getByText(/document-preparation tool/i)).toBeInTheDocument();
    expect(screen.getByText(/does not provide legal advice/i)).toBeInTheDocument();
    expect(screen.getByText(/attorney/i)).toBeInTheDocument();
  });
});
