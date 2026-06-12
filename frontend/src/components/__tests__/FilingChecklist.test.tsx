/**
 * Tests for FilingChecklist component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FilingChecklist } from '../motion/FilingChecklist';

describe('FilingChecklist', () => {
  describe('San Diego County', () => {
    test('renders San Diego courthouse name and address', () => {
      render(<FilingChecklist county="San Diego" motionType="RFO" />);

      expect(screen.getByText(/San Diego Superior Court - Family Court Division/i)).toBeInTheDocument();
      expect(screen.getByText(/1100 Union Street/i)).toBeInTheDocument();
    });

    test('displays filing fee for San Diego', () => {
      render(<FilingChecklist county="San Diego" motionType="RFO" />);

      expect(screen.getByText(/Filing Fee:/)).toBeInTheDocument();
      expect(screen.getAllByText(/\$60/)[0]).toBeInTheDocument();
      expect(screen.getByText(/verify with your local court/i)).toBeInTheDocument();
    });

    test('shows fee-waiver reference FW-001', () => {
      render(<FilingChecklist county="San Diego" motionType="RFO" />);

      expect(screen.getAllByText(/Form FW-001/i)[0]).toBeInTheDocument();
    });

    test('displays copy requirements', () => {
      render(<FilingChecklist county="San Diego" motionType="RFO" />);

      expect(screen.getByText(/Copies Required:/i)).toBeInTheDocument();
      expect(screen.getAllByText(/1 original.*2 copies/i)[0]).toBeInTheDocument();
    });

    test('shows service deadline text', () => {
      render(<FilingChecklist county="San Diego" motionType="RFO" />);

      expect(screen.getByText(/Service Deadline:/i)).toBeInTheDocument();
      expect(screen.getByText(/16 court days before the hearing/i)).toBeInTheDocument();
      expect(screen.getByText(/5 calendar days if serving by mail/i)).toBeInTheDocument();
    });
  });

  describe('Los Angeles County', () => {
    test('renders Los Angeles courthouse name and address', () => {
      render(<FilingChecklist county="Los Angeles" motionType="RFO" />);

      expect(screen.getByText(/Los Angeles Superior Court - Family Court Division/i)).toBeInTheDocument();
    });

    test('displays filing fee for Los Angeles', () => {
      render(<FilingChecklist county="Los Angeles" motionType="RFO" />);

      expect(screen.getByText(/Filing Fee:/)).toBeInTheDocument();
      expect(screen.getAllByText(/\$60/)[0]).toBeInTheDocument();
    });
  });

  describe('Orange County', () => {
    test('renders Orange County courthouse name', () => {
      render(<FilingChecklist county="Orange" motionType="RFO" />);

      expect(screen.getByText(/Orange County Superior Court - Family Court Division/i)).toBeInTheDocument();
    });
  });

  describe('Riverside County', () => {
    test('renders Riverside County courthouse name', () => {
      render(<FilingChecklist county="Riverside" motionType="RFO" />);

      expect(screen.getByText(/Riverside County Superior Court - Family Court Division/i)).toBeInTheDocument();
    });
  });

  describe('Sacramento County', () => {
    test('renders Sacramento County courthouse name', () => {
      render(<FilingChecklist county="Sacramento" motionType="RFO" />);

      expect(screen.getByText(/Sacramento County Superior Court - Family Court Division/i)).toBeInTheDocument();
    });
  });

  describe('Unknown County Fallback', () => {
    test('renders generic checklist for unknown county', () => {
      render(<FilingChecklist county="Unknown County" motionType="RFO" />);

      expect(screen.getByRole('heading', { name: /Generic Filing Checklist/i })).toBeInTheDocument();
      expect(screen.getByText(/verify the specific requirements with your local court/i)).toBeInTheDocument();
    });

    test('provides link to California court self-help center', () => {
      render(<FilingChecklist county="Unknown County" motionType="RFO" />);

      const link = screen.getByRole('link', { name: /California Court self-help center/i });
      expect(link).toHaveAttribute('href', 'https://selfhelp.courts.ca.gov');
      expect(link).toHaveAttribute('target', '_blank');
    });
  });

  describe('Checklist items', () => {
    test('includes all required filing steps', () => {
      render(<FilingChecklist county="San Diego" motionType="RFO" />);

      expect(screen.getByText(/Print 1 original/i)).toBeInTheDocument();
      expect(screen.getByText(/Sign and date/i)).toBeInTheDocument();
      expect(screen.getByText(/Prepare filing fee/i)).toBeInTheDocument();
      expect(screen.getByText(/courthouse address/i)).toBeInTheDocument();
      expect(screen.getByText(/Serve the other party/i)).toBeInTheDocument();
      expect(screen.getByText(/proof of service.*FL-335/i)).toBeInTheDocument();
    });

    test('applies proper styling to checklist items', () => {
      const { container } = render(<FilingChecklist county="San Diego" motionType="RFO" />);

      const checklistItems = container.querySelectorAll('input[type="checkbox"]');
      expect(checklistItems.length).toBeGreaterThan(0);
    });
  });

  describe('Motion type handling', () => {
    test('renders correctly for Response motion type', () => {
      render(<FilingChecklist county="San Diego" motionType="Response" />);

      expect(screen.getByText(/San Diego Superior Court - Family Court Division/i)).toBeInTheDocument();
      expect(screen.getAllByText(/\$60/)[0]).toBeInTheDocument();
    });

    test('renders correctly for different motion types', () => {
      const { rerender } = render(<FilingChecklist county="San Diego" motionType="RFO" />);

      expect(screen.getByText(/Filing Fee:/)).toBeInTheDocument();

      rerender(<FilingChecklist county="San Diego" motionType="OSC" />);

      expect(screen.getByText(/Filing Fee:/)).toBeInTheDocument();
    });
  });
});
