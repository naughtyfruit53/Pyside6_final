// fastapi_migration/frontend/src/context/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '../services/authService';

interface User {
  id: number;
  email: string;
  role: 'super_admin' | 'org_admin' | 'user';
  org_id?: number;
  must_change_password?: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const userData = await authService.getCurrentUser();
          setUser({
            id: userData.id,
            email: userData.email,
            role: userData.role,
            org_id: userData.organization_id,
            must_change_password: userData.must_change_password,
          });
        } catch (error) {
          localStorage.removeItem('token');
          router.push('/login');
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = (token: string) => {
    localStorage.setItem('token', token);
    // Simplified for build - will implement JWT decoding later
    setUser({
      id: 1,
      email: 'demo@example.com',
      role: 'user',
      org_id: 1,
    });
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('orgId');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (undefined === context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};