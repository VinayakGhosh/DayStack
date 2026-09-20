import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '@/contexts/AuthContext';

const ProtectedRoute = () => {
  const { isLoading, isLoggedIn } = useAuth();

  if (isLoading) {
    return (
      <div
        role="status"
        aria-label="Loading session"
        className="flex min-h-screen items-center justify-center bg-background"
      >
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
