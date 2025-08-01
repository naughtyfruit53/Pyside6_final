// frontend/src/context/VoucherContext.tsx

import React, { createContext, useState, ReactNode, useContext } from 'react';

interface VoucherContextType {
  vouchers: any[];
  setVouchers: React.Dispatch<React.SetStateAction<any[]>>;
  addVoucher: (voucher: any) => void;
  updateVoucher: (id: number, updatedVoucher: any) => void;
}

const VoucherContext = createContext<VoucherContextType | undefined>(undefined);

export const VoucherProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [vouchers, setVouchers] = useState<any[]>([]);

  const addVoucher = (voucher: any) => {
    setVouchers((prev) => [...prev, voucher]);
  };

  const updateVoucher = (id: number, updatedVoucher: any) => {
    setVouchers((prev) =>
      prev.map((v) => (v.id === id ? { ...v, ...updatedVoucher } : v))
    );
  };

  const value = {
    vouchers,
    setVouchers,
    addVoucher,
    updateVoucher
  };

  return (
    <VoucherContext.Provider value={value}>
      {children}
    </VoucherContext.Provider>
  );
};

export const useVoucherContext = (): VoucherContextType => {
  const context = useContext(VoucherContext);
  if (!context) {
    throw new Error('useVoucherContext must be used within a VoucherProvider');
  }
  return context;
};