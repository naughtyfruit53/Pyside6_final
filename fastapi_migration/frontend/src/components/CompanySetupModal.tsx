// frontend/src/components/CompanySetupModal.tsx

import React from 'react';
import { Modal, Box, Typography, Button } from '@mui/material'; // Adjust if using different UI library
import { useForm } from 'react-hook-form';
import { createCompany } from '../services/api'; // Import API service
import { useCompany } from '../context/CompanyContext';

interface CompanyFormData {
  name: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  pin_code: string;
  state_code: string;
  gst_number?: string;
  pan_number?: string;
  contact_number: string;
  email?: string;
  logo_path?: string;
}

const CompanySetupModal: React.FC = () => {
  const { setIsCompanySetupNeeded, checkCompanyDetails } = useCompany();
  const { register, handleSubmit, formState: { errors } } = useForm<CompanyFormData>();

  const onSubmit = async (data: CompanyFormData) => {
    try {
      const token = localStorage.getItem('token'); // Assume token stored after login
      await createCompany(data, token);
      setIsCompanySetupNeeded(false);
      checkCompanyDetails(); // Re-check to confirm
    } catch (error) {
      console.error('Error saving company details:', error);
      // Handle error (e.g., show toast)
    }
  };

  return (
    <Modal open={true} onClose={() => {}} disableEscapeKeyDown> {/* Persist until saved */}
      <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 400, bgcolor: 'background.paper', p: 4 }}>
        <Typography variant="h6">Setup Company Details</Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <input placeholder="Name" {...register('name', { required: true })} />
          {errors.name && <span>Required</span>}
          <input placeholder="Address 1" {...register('address1', { required: true })} />
          {errors.address1 && <span>Required</span>}
          <input placeholder="Address 2" {...register('address2')} />
          <input placeholder="City" {...register('city', { required: true })} />
          {errors.city && <span>Required</span>}
          <input placeholder="State" {...register('state', { required: true })} />
          {errors.state && <span>Required</span>}
          <input placeholder="Pin Code" {...register('pin_code', { required: true })} />
          {errors.pin_code && <span>Required</span>}
          <input placeholder="State Code" {...register('state_code', { required: true })} />
          {errors.state_code && <span>Required</span>}
          <input placeholder="GST Number" {...register('gst_number')} />
          <input placeholder="PAN Number" {...register('pan_number')} />
          <input placeholder="Contact Number" {...register('contact_number', { required: true })} />
          {errors.contact_number && <span>Required</span>}
          <input placeholder="Email" {...register('email')} />
          <input placeholder="Logo Path" {...register('logo_path')} />
          <Button type="submit">Save</Button>
        </form>
      </Box>
    </Modal>
  );
};

export default CompanySetupModal;