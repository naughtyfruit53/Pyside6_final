// fastapi_migration/frontend/src/pages/admin/index.tsx

import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import Link from 'next/link';
import RoleGate from '../components/RoleGate';

const AdminDashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <RoleGate allowedRoles={['super_admin', 'org_admin']}>
      <div>
        <h1>Admin Dashboard</h1>
        {user?.role === 'super_admin' && (
          <>
            <Link href="/admin/organizations"><Button>Manage Organizations</Button></Link>
            <Link href="/admin/users"><Button>Manage Users</Button></Link>
          </>
        )}
        {/* Add other dashboard elements */}
      </div>
    </RoleGate>
  );
};

export default AdminDashboard;