import { useEffect } from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from './ProtectedRoute';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);

const renderProtectedRoute = (onMount = vi.fn()) => {
  const ProtectedPage = () => {
    useEffect(() => {
      onMount();
    }, []);

    return <p>Protected content</p>;
  };

  render(
    <MemoryRouter initialEntries={['/projects']}>
      <Routes>
        <Route path="/login" element={<p>Login page</p>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/projects" element={<ProtectedPage />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );

  return onMount;
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  it('does not mount protected pages while session restoration is pending', () => {
    mockedUseAuth.mockReturnValue({ isLoading: true, isLoggedIn: false } as ReturnType<typeof useAuth>);
    const onMount = renderProtectedRoute();

    expect(screen.getByRole('status', { name: 'Loading session' })).toBeInTheDocument();
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
    expect(onMount).not.toHaveBeenCalled();
  });

  it('redirects signed-out members without mounting the protected page', () => {
    mockedUseAuth.mockReturnValue({ isLoading: false, isLoggedIn: false } as ReturnType<typeof useAuth>);
    const onMount = renderProtectedRoute();

    expect(screen.getByText('Login page')).toBeInTheDocument();
    expect(onMount).not.toHaveBeenCalled();
  });

  it('mounts the protected page after session restoration succeeds', () => {
    mockedUseAuth.mockReturnValue({ isLoading: false, isLoggedIn: true } as ReturnType<typeof useAuth>);
    const onMount = renderProtectedRoute();

    expect(screen.getByText('Protected content')).toBeInTheDocument();
    expect(onMount).toHaveBeenCalledOnce();
  });
});
