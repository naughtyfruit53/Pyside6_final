// frontend/src/components/CompanySetupModal.tsx

import React, { useState } from 'react';
import { Modal, Box, Typography, Button, TextField, Alert, CircularProgress, Grid } from '@mui/material';
import { useForm } from 'react-hook-form';
import { companyService } from '../services/authService';
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
  const { isCompanySetupNeeded, setIsCompanySetupNeeded, checkCompanyDetails } = useCompany();
  const { register, handleSubmit, formState: { errors } } = useForm<CompanyFormData>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const onSubmit = async (data: CompanyFormData) => {
    setLoading(true);
    setError(null);

    // Map frontend field names to expected backend schema fields
    const mappedData = {
      name: data.name,
      address_line1: data.address1,
      address_line2: data.address2,
      city: data.city,
      state: data.state,
      pin_code: data.pin_code,
      state_code: data.state_code,
      gstin: data.gst_number,
      pan: data.pan_number,
      contact_phone: data.contact_number,
      email: data.email,
      logo_path: data.logo_path,
    };

    try {
      await companyService.createCompany(mappedData);
      setSuccess(true);
      setIsCompanySetupNeeded(false);
      checkCompanyDetails();
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 2000);
    } catch (error: any) {
      setError(error.userMessage || 'Error saving company details');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={isCompanySetupNeeded} onClose={() => {}} disableEscapeKeyDown={!success}>
      <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 600, bgcolor: 'background.paper', p: 4 }}>
        <Typography variant="h6">Setup Company Details</Typography>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mt: 2 }}>Company details saved successfully! Redirecting...</Alert>}
        {!success && (
          <form onSubmit={handleSubmit(onSubmit)}>
            <Grid container spacing={2} sx={{ mt: 2 }}>
              <Grid item xs={12}>
                <TextField label="Name" {...register('name', { required: 'Name is required' })} fullWidth error={!!errors.name} helperText={errors.name?.message} />
              </Grid>
              <Grid item xs={12}>
                <TextField label="Address 1" {...register('address1', { required: 'Address 1 is required' })} fullWidth error={!!errors.address1} helperText={errors.address1?.message} />
              </Grid>
              <Grid item xs={12}>
                <TextField label="Address 2" {...register('address2')} fullWidth />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="City" {...register('city', { required: 'City is required' })} fullWidth error={!!errors.city} helperText={errors.city?.message} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="State" {...register('state', { required: 'State is required' })} fullWidth error={!!errors.state} helperText={errors.state?.message} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="Pin Code" {...register('pin_code', { required: 'Pin Code is required' })} fullWidth error={!!errors.pin_code} helperText={errors.pin_code?.message} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="State Code" {...register('state_code', { required: 'State Code is required' })} fullWidth error={!!errors.state_code} helperText={errors.state_code?.message} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="GST Number" {...register('gst_number')} fullWidth />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="PAN Number" {...register('pan_number')} fullWidth />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="Contact Number" {...register('contact_number', { required: 'Contact Number is required' })} fullWidth error={!!errors.contact_number} helperText={errors.contact_number?.message} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="Email" {...register('email')} fullWidth />
              </Grid>
              <Grid item xs={12}>
                <TextField label="Logo Path" {...register('logo_path')} fullWidth />
              </Grid>
            </Grid>
            <Button type="submit" variant="contained" disabled={loading} sx={{ mt: 2 }}>
              {loading ? <CircularProgress size={24} /> : 'Save'}
            </Button>
          </form>
        )}
      </Box>
    </Modal>
  );
};

export default CompanySetupModal;