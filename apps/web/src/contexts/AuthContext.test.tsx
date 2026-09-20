import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { authApi, SESSION_EXPIRED_EVENT } from '@/lib/api';
import { AuthProvider, useAuth } from './AuthContext';

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    authApi: {
      ...actual.authApi,
      getProfile: vi.fn(),
    },
  };
});

describe('AuthProvider session expiry', () => {
  beforeEach(() => {
    vi.mocked(authApi.getProfile).mockReset();
  });

  it('signs out an authenticated member when refresh also expires', async () => {
    vi.mocked(authApi.getProfile).mockResolvedValue({
      data: {
        member_id: 'member-1',
        email: 'member@example.com',
        display_name: 'Member',
        time_zone: 'UTC',
      },
    });
    const AuthState = () => {
      const { isLoading, isLoggedIn } = useAuth();
      return <p>{isLoading ? 'Loading' : isLoggedIn ? 'Signed in' : 'Signed out'}</p>;
    };
    render(<AuthProvider><AuthState /></AuthProvider>);

    expect(await screen.findByText('Signed in')).toBeInTheDocument();

    act(() => window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT)));

    expect(await screen.findByText('Signed out')).toBeInTheDocument();
  });
});
