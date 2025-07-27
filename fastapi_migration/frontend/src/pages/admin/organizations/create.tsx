// fastapi_migration/frontend/src/pages/admin/organizations/create.tsx

import React from 'react';
import { useRouter } from 'next/router';
import OrganizationForm from '../../../components/OrganizationForm';
import api from '../../../utils/api';
import RoleGate from '../../../components/RoleGate';

const CreateOrganizationPage: React.FC = () => {
  const router = useRouter();

  const handleSubmit = async (data: any) => {
    try {
      await api.post('/organizations', data);
      router.push('/admin/organizations');
    } catch (error) {
      console.error('Failed to create organization', error);
    }
  };

  return (
    <RoleGate allowedRoles={['super_admin']}>
      <div>
        <h1>Create New Organization</h1>
        <OrganizationForm onSubmit={handleSubmit} />
      </div>
    </RoleGate>
  );
};

export default CreateOrganizationPage;