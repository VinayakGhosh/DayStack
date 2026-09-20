import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, Member, SESSION_EXPIRED_EVENT } from '@/lib/api';

interface AuthContextType {
  user: Member | null;
  isLoading: boolean;
  isLoggedIn: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (data: { first_name: string; last_name: string; email: string; password: string }) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<Member | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    const { data } = await authApi.getProfile();
    if (data) {
      setUser(data);
    } else {
      setUser(null);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    const handleSessionExpired = () => {
      setUser(null);
      setIsLoading(false);
    };

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    refreshUser();

    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
  }, []);

  const login = async (email: string, password: string) => {
    const { data, error } = await authApi.login(email, password);
    if (data) {
      setUser(data);
      return { success: true };
    }
    return { success: false, error: error || 'Login failed' };
  };

  const register = async (data: { first_name: string; last_name: string; email: string; password: string }) => {
    const { data: member, error } = await authApi.register({
      display_name: `${data.first_name.trim()} ${data.last_name.trim()}`.trim(),
      email: data.email,
      password: data.password,
      time_zone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    });
    if (member) {
      setUser(member);
      return { success: true };
    }
    return { success: false, error };
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isLoggedIn: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
