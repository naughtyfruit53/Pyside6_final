import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Grid
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { companyService } from '../services/authService';
import axios from 'axios';

interface CompanyDetailsModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  isRequired?: boolean;
}

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
}

const stateToCodeMap: { [key: string]: string } = {
  'Andhra Pradesh': '37',
  'Arunachal Pradesh': '12',
  'Assam': '18',
  'Bihar': '10',
  'Chhattisgarh': '22',
  'Goa': '30',
  'Gujarat': '24',
  'Haryana': '06',
  'Himachal Pradesh': '02',
  'Jammu and Kashmir': '01',
  'Jharkhand': '20',
  'Karnataka': '29',
  'Kerala': '32',
  'Madhya Pradesh': '23',
  'Maharashtra': '27',
  'Manipur': '14',
  'Meghalaya': '17',
  'Mizoram': '15',
  'Nagaland': '13',
  'Odisha': '21',
  'Punjab': '03',
  'Rajasthan': '08',
  'Sikkim': '11',
  'Tamil Nadu': '33',
  'Telangana': '36',
  'Tripura': '16',
  'Uttar Pradesh': '09',
  'Uttarakhand': '05',
  'West Bengal': '19',
  'Andaman and Nicobar Islands': '35',
  'Chandigarh': '04',
  'Dadra and Nagar Haveli and Daman and Diu': '26',
  'Lakshadweep': '31',
  'Delhi': '07',
  'Puducherry': '34',
  'Ladakh': '38',
};

const CompanyDetailsModal: React.FC<CompanyDetailsModalProps> = ({
  open,
  onClose,
  onSuccess,
  isRequired = false
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch
  } = useForm<CompanyFormData>();

  const pinCode = watch('pin_code');
  const state = watch('state');
  const city = watch('city');

  useEffect(() => {
    if (pinCode && pinCode.length === 6 && /^\d{6}$/.test(pinCode)) {
      fetchLocationData(pinCode);
    }
  }, [pinCode]);

  useEffect(() => {
    if (state) {
      const code = stateToCodeMap[state];
      if (code) {
        setValue('state_code', code);
      }
    }
  }, [state, city, setValue]);

  const fetchLocationData = async (pin: string) => {
    try {
      const response = await axios.get(`https://api.postalpincode.in/pincode/${pin}`);
      const data = response.data[0];
      if (data.Status === 'Success' && data.PostOffice && data.PostOffice.length > 0) {
        const postOffice = data.PostOffice[0];
        setValue('city', postOffice.District, { shouldValidate: true });
        setValue('state', postOffice.State, { shouldValidate: true });
      } else {
        setError('Invalid PIN code');
      }
    } catch (err) {
      setError('Failed to fetch location data');
    }
  };

  const handleClose = () => {
    if (!isRequired || success) {
      reset();
      setError(null);
      setSuccess(false);
      setFieldErrors({});
      onClose();
    }
  };

  const onSubmit = async (data: CompanyFormData) => {
    setLoading(true);
    setError(null);
    setFieldErrors({});

    // Correct mapping to backend schema fields
    const mappedData = {
      name: data.name,
      address1: data.address1,
      address2: data.address2,
      city: data.city,
      state: data.state,
      pin_code: data.pin_code,
      state_code: data.state_code,
      gst_number: data.gst_number,
      pan_number: data.pan_number,
      contact_number: data.contact_number,
      email: data.email,
    };

    try {
      await companyService.createCompany(mappedData);
      setSuccess(true);
      if (onSuccess) {
        onSuccess();
      }
      if (!isRequired) {
        setTimeout(() => {
          handleClose();
        }, 2000);
      }
    } catch (err: any) {
      if (err.status === 422 && err.response?.data?.detail) {
        const validationErrors = err.response.data.detail;
        const newFieldErrors: { [key: string]: string } = {};
        validationErrors.forEach((validationError: any) => {
          const field = validationError.loc[validationError.loc.length - 1];
          newFieldErrors[field] = validationError.msg;
        });
        setFieldErrors(newFieldErrors);
        setError('Please correct the errors below');
      } else {
        setError(err.userMessage || 'Failed to create company details');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="md" 
      fullWidth
      disableEscapeKeyDown={isRequired && !success}
    >
      <DialogTitle>
        {isRequired ? 'Complete Company Information' : 'Company Details'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {isRequired && !success && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Please complete your company information to continue using the system.
            </Alert>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Company details created successfully!
              {isRequired && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  You can now access all features of the system.
                </Typography>
              )}
            </Alert>
          )}

          {!success && (
            <form onSubmit={handleSubmit(onSubmit)}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Company Name"
                    {...register('name', { required: 'Company name is required' })}
                    error={!!errors.name || !!fieldErrors.name}
                    helperText={errors.name?.message || fieldErrors.name}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Address Line 1"
                    {...register('address1', { required: 'Address is required' })}
                    error={!!errors.address1 || !!fieldErrors.address1}
                    helperText={errors.address1?.message || fieldErrors.address1}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Address Line 2"
                    {...register('address2')}
                    error={!!fieldErrors.address2}
                    helperText={fieldErrors.address2}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Pin Code"
                    {...register('pin_code', {
                      required: 'Pin code is required',
                      pattern: {
                        value: /^\d{6}$/,
                        message: 'Pin code must be 6 digits'
                      }
                    })}
                    error={!!errors.pin_code || !!fieldErrors.pin_code}
                    helperText={errors.pin_code?.message || fieldErrors.pin_code}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="City"
                    {...register('city', { required: 'City is required' })}
                    error={!!errors.city || !!fieldErrors.city}
                    helperText={errors.city?.message || fieldErrors.city}
                    disabled={loading}
                    InputProps={{
                      readOnly: true,  // Make readonly
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="State"
                    {...register('state', { required: 'State is required' })}
                    error={!!errors.state || !!fieldErrors.state}
                    helperText={errors.state?.message || fieldErrors.state}
                    disabled={loading}
                    InputProps={{
                      readOnly: true,  // Make readonly
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="State Code"
                    {...register('state_code', {
                      required: 'State code is required',
                      pattern: {
                        value: /^\d{2}$/,
                        message: 'State code must be 2 digits'
                      }
                    })}
                    error={!!errors.state_code || !!fieldErrors.state_code}
                    helperText={errors.state_code?.message || fieldErrors.state_code}
                    disabled={loading}
                    InputProps={{
                      readOnly: true,  // Make readonly if auto-populated
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="GST Number"
                    {...register('gst_number')}
                    error={!!fieldErrors.gst_number}
                    helperText={fieldErrors.gst_number}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="PAN Number"
                    {...register('pan_number')}
                    error={!!fieldErrors.pan_number}
                    helperText={fieldErrors.pan_number}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Contact Number"
                    {...register('contact_number', { required: 'Contact number is required' })}
                    error={!!errors.contact_number || !!fieldErrors.contact_number}
                    helperText={errors.contact_number?.message || fieldErrors.contact_number}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    {...register('email', {
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address'
                      }
                    })}
                    error={!!errors.email || !!fieldErrors.email}
                    helperText={errors.email?.message || fieldErrors.email}
                    disabled={loading}
                  />
                </Grid>
              </Grid>
            </form>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        {!isRequired && (
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
        )}
        {success && isRequired && (
          <Button onClick={handleClose} variant="contained">
            Continue
          </Button>
        )}
        {!success && (
          <Button
            onClick={handleSubmit(onSubmit)}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            Save Company Details
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default CompanyDetailsModal;