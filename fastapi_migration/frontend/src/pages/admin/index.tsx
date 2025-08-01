// fastapi_migration/frontend/src/pages/admin/index.tsx

import React from 'react';
// import { useAuth } from '../context/AuthContext';
import Link from 'next/link';
// import RoleGate from '../components/RoleGate';

const AdminDashboard: React.FC = () => {
  // const { user } = useAuth();

  return (
    <div>
      {/* <RoleGate allowedRoles={['super_admin', 'org_admin']}> */}
        <div>
          <h1>Admin Dashboard</h1>
          <p>Temporarily simplified for build testing</p>
          {/* {user?.role === 'super_admin' && (
            <>
              <Link href="/admin/organizations"><Button>Manage Organizations</Button></Link>
              <Link href="/admin/users"><Button>Manage Users</Button></Link>
            </>
          )} */}
          {/* Add other dashboard elements */}
        </div>
      {/* </RoleGate> */}
    </div>
  );
};

export default AdminDashboard;