// frontend/src/services/vouchersService.ts

import api from './api';

export const voucherService = {
  // Purchase Vouchers
  getPurchaseVoucherById: async (id: number) => {
    const response = await api.get(`/vouchers/purchase-vouchers/${id}`);
    return response.data;
  },
  createPurchaseVoucher: async (data: any, sendEmail: boolean) => {
    const response = await api.post(`/vouchers/purchase-vouchers/`, data, { params: { send_email: sendEmail } });
    return response.data;
  },
  updatePurchaseVoucher: async (id: number, data: any) => {
    const response = await api.put(`/vouchers/purchase-vouchers/${id}`, data);
    return response.data;
  },

  // Purchase Orders
  getPurchaseOrderById: async (id: number) => {
    const response = await api.get(`/vouchers/purchase_order/${id}`);
    return response.data;
  },
  createPurchaseOrder: async (data: any, sendEmail: boolean) => {
    const response = await api.post(`/vouchers/purchase_order/`, data, { params: { send_email: sendEmail } });
    return response.data;
  },
  updatePurchaseOrder: async (id: number, data: any) => {
    const response = await api.put(`/vouchers/purchase_order/${id}`, data);
    return response.data;
  },

  // GRN
  getGrnById: async (id: number) => {
    const response = await api.get(`/vouchers/grn/${id}`);
    return response.data;
  },
  createGrn: async (data: any, sendEmail: boolean) => {
    const response = await api.post(`/vouchers/grn/`, data, { params: { send_email: sendEmail } });
    return response.data;
  },
  updateGrn: async (id: number, data: any) => {
    const response = await api.put(`/vouchers/grn/${id}`, data);
    return response.data;
  },

  // Rejection In
  getRejectionInById: async (id: number) => {
    const response = await api.get(`/vouchers/rejection_in/${id}`);
    return response.data;
  },
  createRejectionIn: async (data: any, sendEmail: boolean) => {
    const response = await api.post(`/vouchers/rejection_in/`, data, { params: { send_email: sendEmail } });
    return response.data;
  },
  updateRejectionIn: async (id: number, data: any) => {
    const response = await api.put(`/vouchers/rejection_in/${id}`, data);
    return response.data;
  },
};