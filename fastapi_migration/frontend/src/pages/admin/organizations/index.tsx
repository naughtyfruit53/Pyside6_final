// fastapi_migration/frontend/src/pages/admin/organizations/index.tsx

import React, { useEffect, useState } from 'react';
// import { useAuth } from '../../context/AuthContext';
// import OrganizationList from '../../components/OrganizationList';
// import api from '../../utils/api';
// import RoleGate from '../../components/RoleGate';

interface Organization {
  id: number;
  name: string;
  // Add other fields as per backend model
}

const OrganizationsPage: React.FC = () => {
  // const { user } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);

  // Temporarily simplified for build testing
  useEffect(() => {
    setLoading(false);
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {/* <RoleGate allowedRoles={['super_admin']}> */}
        <div>
          <h1>Organizations Management</h1>
          <p>Temporarily simplified for build testing</p>
          {/* <OrganizationList organizations={organizations} onRefresh={fetchOrganizations} /> */}
        </div>
      {/* </RoleGate> */}
    </div>
  );
};

export default OrganizationsPage;