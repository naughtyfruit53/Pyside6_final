// fastapi_migration/frontend/src/pages/admin/organizations/index.tsx

import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import OrganizationList from '../../components/OrganizationList';
import api from '../../utils/api';
import RoleGate from '../../components/RoleGate';

interface Organization {
  id: number;
  name: string;
  // Add other fields as per backend model
}

const OrganizationsPage: React.FC = () => {
  const { user } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchOrganizations();
    }
  }, [user]);

  const fetchOrganizations = async () => {
    try {
      const response = await api.get('/organizations');
      setOrganizations(response.data);
    } catch (error) {
      console.error('Failed to fetch organizations', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <RoleGate allowedRoles={['super_admin']}>
      <div>
        <h1>Organizations Management</h1>
        <OrganizationList organizations={organizations} onRefresh={fetchOrganizations} />
      </div>
    </RoleGate>
  );
};

export default OrganizationsPage;