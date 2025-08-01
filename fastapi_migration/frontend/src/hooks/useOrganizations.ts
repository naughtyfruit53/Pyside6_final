// fastapi_migration/frontend/src/hooks/useOrganization.ts

import { useEffect, useState } from 'react';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';

export const useOrganizations = () => {
  const { user } = useAuth();
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      api.get('/organizations').then(res => {
        setOrganizations(res.data);
        setLoading(false);
      }).catch(err => {
        console.error(err);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [user]);

  return { organizations, loading };
};