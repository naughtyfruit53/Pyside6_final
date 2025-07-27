// fastapi_migration/frontend/src/contexts/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import jwtDecode from '../utils/jwt-decode';
import api from '../utils/api';

interface User {
  id: number;
  email: string;
  role: 'super_admin' | 'org_admin' | 'user';
  org_id?: number;
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

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded: any = jwtDecode(token);
        setUser({
          id: decoded.sub || 1,
          email: decoded.email || 'demo@example.com',
          role: decoded.role || 'user',
          org_id: decoded.organization_id,
        });
        localStorage.setItem('orgId', decoded.organization_id?.toString() || 'null');
      } catch (error) {
        console.error('Invalid token');
        logout();
      }
    }
    setLoading(false);
  }, []);

  const login = (token: string) => {
    localStorage.setItem('token', token);
    try {
      const decoded: any = jwtDecode(token);
      setUser({
        id: decoded.sub || 1,
        email: decoded.email || 'demo@example.com',
        role: decoded.role || 'user',
        org_id: decoded.organization_id,
      });
      localStorage.setItem('orgId', decoded.organization_id?.toString() || 'null');
    } catch (error) {
      console.error('Failed to decode token');
    }
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