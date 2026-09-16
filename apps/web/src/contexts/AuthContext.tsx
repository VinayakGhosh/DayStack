import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, User, setToken, clearToken, isAuthenticated } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isLoggedIn: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (data: { first_name: string; last_name: string; email: string; password: string }) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    if (!isAuthenticated()) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    const { data, error } = await authApi.getProfile();
    if (data) {
      setUser(data);
    } else if (error) {
      clearToken();
      setUser(null);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (email: string, password: string) => {
    const { data, error } = await authApi.login(email, password);
    if (data?.access_token) {
      setToken(data.access_token);
      await refreshUser();
      return { success: true };
    }
    return { success: false, error: error || 'Login failed' };
  };

  const register = async (data: { first_name: string; last_name: string; email: string; password: string }) => {
    const { error } = await authApi.register(data);
    if (!error) {
      return { success: true };
    }
    return { success: false, error };
  };

  const logout = () => {
    clearToken();
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
