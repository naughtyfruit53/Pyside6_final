// fastapi_migration/frontend/src/contexts/OrganizationContext.tsx

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface OrganizationContextType {
  orgId: number | null;
  setOrgId: (id: number | null) => void;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const [orgId, setOrgId] = useState<number | null>(null);

  return (
    <OrganizationContext.Provider value={{ orgId, setOrgId }}>
      {children}
    </OrganizationContext.Provider>
  );
}

export const useOrganization = () => {
  const context = useContext(OrganizationContext);
  if (undefined === context) {
    throw new Error('useOrganization must be used within OrganizationProvider');
  }
  return context;
};