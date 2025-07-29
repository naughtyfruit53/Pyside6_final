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
  CircularProgress
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { organizationService } from '../services/authService';

interface CreateOrganizationLicenseModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (result: any) => void;
}

interface LicenseFormData {
  organization_name: string;
  superadmin_email: string;
}

const CreateOrganizationLicenseModal: React.FC<CreateOrganizationLicenseModalProps> = ({
  open,
  onClose,
  onSuccess
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<any | null>(null);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<LicenseFormData>();

  const handleClose = () => {
    reset();
    setError(null);
    setSuccess(null);
    onClose();
  };

  const onSubmit = async (data: LicenseFormData) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await organizationService.createLicense(data);
      setSuccess(result);
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create organization license');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Organization License</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                <strong>License created successfully!</strong>
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Organization:</strong> {success.organization_name}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Subdomain:</strong> {success.subdomain}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Admin Email:</strong> {success.superadmin_email}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Temporary Password:</strong> {success.temp_password}
              </Typography>
              <Typography variant="body2" color="warning.main" sx={{ mt: 1 }}>
                Please save these details securely. The password should be changed on first login.
              </Typography>
            </Alert>
          )}

          {!success && (
            <form onSubmit={handleSubmit(onSubmit)}>
              <TextField
                fullWidth
                label="Organization Name"
                margin="normal"
                {...register('organization_name', {
                  required: 'Organization name is required',
                  minLength: {
                    value: 3,
                    message: 'Organization name must be at least 3 characters'
                  }
                })}
                error={!!errors.organization_name}
                helperText={errors.organization_name?.message}
                disabled={loading}
              />

              <TextField
                fullWidth
                label="Superadmin Email"
                type="email"
                margin="normal"
                {...register('superadmin_email', {
                  required: 'Superadmin email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
                error={!!errors.superadmin_email}
                helperText={errors.superadmin_email?.message}
                disabled={loading}
              />

              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  This will create a new organization with a trial license and a superadmin user account.
                  A confirmation email will be sent with login details.
                </Typography>
              </Box>
            </form>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          {success ? 'Close' : 'Cancel'}
        </Button>
        {!success && (
          <Button
            onClick={handleSubmit(onSubmit)}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            Create License
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default CreateOrganizationLicenseModal;