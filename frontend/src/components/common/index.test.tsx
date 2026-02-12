import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingState, EmptyState, PageHeader } from './index';

describe('LoadingState', () => {
  it('renders with default message', () => {
    render(<LoadingState />);
    expect(screen.getByText(/Cargando/i)).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<LoadingState message="Loading tickets..." />);
    expect(screen.getByText('Loading tickets...')).toBeInTheDocument();
  });

  it('displays spinner animation', () => {
    const { container } = render(<LoadingState />);
    const spinner = container.querySelector('.spinner');
    expect(spinner).toBeInTheDocument();
  });
});

describe('EmptyState', () => {
  it('renders with provided message', () => {
    render(<EmptyState message="No items found" />);
    expect(screen.getByText('No items found')).toBeInTheDocument();
  });

  it('renders with default icon', () => {
    const { container } = render(<EmptyState message="Empty" />);
    const icon = container.querySelector('.empty-icon');
    expect(icon).toHaveTextContent('📭');
  });

  it('renders with custom icon', () => {
    const { container } = render(<EmptyState message="Empty" icon="🎫" />);
    const icon = container.querySelector('.empty-icon');
    expect(icon).toHaveTextContent('🎫');
  });
});

describe('PageHeader', () => {
  it('renders title', () => {
    render(<PageHeader title="Test Title" />);
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<PageHeader title="Title" subtitle={<p>Subtitle text</p>} />);
    expect(screen.getByText('Subtitle text')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', () => {
    const { container } = render(<PageHeader title="Title" />);
    const subtitle = container.querySelector('p');
    expect(subtitle).not.toBeInTheDocument();
  });

  it('applies correct CSS classes', () => {
    const { container } = render(<PageHeader title="Title" />);
    expect(container.querySelector('.page-header')).toBeInTheDocument();
    expect(container.querySelector('.page-title')).toBeInTheDocument();
  });
});
