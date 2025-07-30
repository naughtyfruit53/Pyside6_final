// frontend/src/context/CompanyContext.tsx

import React, { createContext, useState, useContext, useEffect } from 'react';
import { companyService } from '../services/authService';

interface CompanyContextType {
  isCompanySetupNeeded: boolean;
  setIsCompanySetupNeeded: React.Dispatch<React.SetStateAction<boolean>>;
  checkCompanyDetails: () => Promise<void>;
}

const CompanyContext = createContext<CompanyContextType | undefined>(undefined);

export const CompanyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isCompanySetupNeeded, setIsCompanySetupNeeded] = useState(false);

  const checkCompanyDetails = async () => {
    try {
      await companyService.getCurrentCompany();
      setIsCompanySetupNeeded(false);
    } catch (error: any) {
      if (error.status === 404) {
        setIsCompanySetupNeeded(true);
      } else {
        console.error('Error checking company details:', error);
      }
    }
  };

  useEffect(() => {
    if (localStorage.getItem('token')) {
      checkCompanyDetails();
    }
  }, []);

  return (
    <CompanyContext.Provider value={{ isCompanySetupNeeded, setIsCompanySetupNeeded, checkCompanyDetails }}>
      {children}
    </CompanyContext.Provider>
  );
};

export const useCompany = () => {
  const context = useContext(CompanyContext);
  if (undefined === context) {
    throw new Error('useCompany must be used within a CompanyProvider');
  }
  return context;
};