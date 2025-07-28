// frontend/src/hooks/useVouchers.ts

import { useQuery, useMutation } from 'react-query';
import { voucherService } from '../services/vouchersService';

export const usePurchaseVouchers = (id?: number) => {
  return useQuery(
    ['purchaseVoucher', id],
    () => voucherService.getPurchaseVoucherById(id!),
    { enabled: !!id }
  );
};

export const usePurchaseOrders = (id?: number) => {
  return useQuery(
    ['purchaseOrder', id],
    () => voucherService.getPurchaseOrderById(id!),
    { enabled: !!id }
  );
};

export const useGrns = (id?: number) => {
  return useQuery(
    ['grn', id],
    () => voucherService.getGrnById(id!),
    { enabled: !!id }
  );
};

export const useRejectionIns = (id?: number) => {
  return useQuery(
    ['rejectionIn', id],
    () => voucherService.getRejectionInById(id!),
    { enabled: !!id }
  );
};

// Mutations can be added similarly if needed