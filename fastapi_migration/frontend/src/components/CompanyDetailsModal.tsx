import React, { useState } from 'react';
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
  Grid,
  MenuItem
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { organizationService } from '../services/authService';

interface CompanyDetailsModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  isRequired?: boolean;
}

interface CompanyFormData {
  name: string;
  business_type: string;
  industry: string;
  website: string;
  primary_email: string;
  primary_phone: string;
  address1: string;
  address2: string;
  city: string;
  state: string;
  pin_code: string;
  gst_number: string;
  pan_number: string;
}

const businessTypes = [
  'Manufacturing',
  'Trading',
  'Service',
  'Retail',
  'Wholesale',
  'Other'
];

const industries = [
  'Automotive',
  'Electronics',
  'Textiles',
  'Food & Beverages',
  'Healthcare',
  'IT Services',
  'Construction',
  'Real Estate',
  'Education',
  'Other'
];

const CompanyDetailsModal: React.FC<CompanyDetailsModalProps> = ({
  open,
  onClose,
  onSuccess,
  isRequired = false
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<CompanyFormData>();

  const handleClose = () => {
    if (!isRequired || success) {
      reset();
      setError(null);
      setSuccess(false);
      onClose();
    }
  };

  const onSubmit = async (data: CompanyFormData) => {
    setLoading(true);
    setError(null);

    try {
      await organizationService.updateOrganization(data);
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
      setError(err.message || 'Failed to update company details');
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
              Company details updated successfully!
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
                    error={!!errors.name}
                    helperText={errors.name?.message}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    select
                    label="Business Type"
                    {...register('business_type', { required: 'Business type is required' })}
                    error={!!errors.business_type}
                    helperText={errors.business_type?.message}
                    disabled={loading}
                  >
                    {businessTypes.map((type) => (
                      <MenuItem key={type} value={type}>
                        {type}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    select
                    label="Industry"
                    {...register('industry')}
                    disabled={loading}
                  >
                    {industries.map((industry) => (
                      <MenuItem key={industry} value={industry}>
                        {industry}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Website"
                    type="url"
                    {...register('website')}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Primary Email"
                    type="email"
                    {...register('primary_email', {
                      required: 'Primary email is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address'
                      }
                    })}
                    error={!!errors.primary_email}
                    helperText={errors.primary_email?.message}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Primary Phone"
                    {...register('primary_phone', { required: 'Primary phone is required' })}
                    error={!!errors.primary_phone}
                    helperText={errors.primary_phone?.message}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Address Line 1"
                    {...register('address1', { required: 'Address is required' })}
                    error={!!errors.address1}
                    helperText={errors.address1?.message}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Address Line 2"
                    {...register('address2')}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="City"
                    {...register('city', { required: 'City is required' })}
                    error={!!errors.city}
                    helperText={errors.city?.message}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="State"
                    {...register('state', { required: 'State is required' })}
                    error={!!errors.state}
                    helperText={errors.state?.message}
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
                    error={!!errors.pin_code}
                    helperText={errors.pin_code?.message}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="GST Number"
                    {...register('gst_number')}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="PAN Number"
                    {...register('pan_number')}
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