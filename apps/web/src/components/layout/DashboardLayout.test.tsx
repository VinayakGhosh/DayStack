import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import DashboardLayout from './DashboardLayout';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    isLoggedIn: true,
    isLoading: false,
    logout: vi.fn(),
    user: { display_name: 'Asha Rao', email: 'asha@example.com' },
  }),
}));

describe('DashboardLayout', () => {
  it('keeps member navigation focused on Today, Projects, and Settings', () => {
    render(
      <MemoryRouter initialEntries={['/today']}>
        <DashboardLayout><p>Today content</p></DashboardLayout>
      </MemoryRouter>,
    );

    expect(screen.getAllByRole('link', { name: 'Today' }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('link', { name: 'Projects' }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('link', { name: 'Settings' }).length).toBeGreaterThan(0);
    expect(screen.queryByRole('link', { name: 'Subscription' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Dashboard' })).not.toBeInTheDocument();
  });
});
