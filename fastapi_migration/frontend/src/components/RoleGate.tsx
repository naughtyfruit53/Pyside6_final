// fastapi_migration/frontend/src/components/RoleGate.tsx

import React, { ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';

interface RoleGateProps {
  allowedRoles: string[];
  children: ReactNode;
}

const RoleGate: React.FC<RoleGateProps> = ({ allowedRoles, children }) => {
  const { user } = useAuth();
  const router = useRouter();

  if (!user || !allowedRoles.includes(user.role)) {
    router.push('/login');
    return null;
  }

  return <>{children}</>;
};

export default RoleGate;