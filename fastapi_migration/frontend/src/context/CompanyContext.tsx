// frontend/src/context/CompanyContext.tsx

import React, { createContext, useState, useContext } from 'react';
import { getCurrentCompany } from '../services/api'; // Import API service

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
      const token = localStorage.getItem('token');
      await getCurrentCompany(token);
      setIsCompanySetupNeeded(false);
    } catch (error) {
      if (error.response?.status === 404) {
        setIsCompanySetupNeeded(true);
      } else {
        console.error('Error checking company details:', error);
      }
    }
  };

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