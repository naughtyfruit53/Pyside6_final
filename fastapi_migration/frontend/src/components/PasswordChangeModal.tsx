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
import { passwordService } from '../services/authService';

interface PasswordChangeModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  isRequired?: boolean; // For mandatory password changes
}

interface PasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const PasswordChangeModal: React.FC<PasswordChangeModalProps> = ({
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
    reset,
    watch,
    getValues
  } = useForm<PasswordFormData>();

  const newPassword = watch('newPassword');

  const handleClose = () => {
    if (!isRequired || success) {
      reset();
      setError(null);
      setSuccess(false);
      onClose();
    }
  };

  const onSubmit = async (data: PasswordFormData) => {
    setLoading(true);
    setError(null);

    try {
      await passwordService.changePassword(data.currentPassword, data.newPassword);
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
      // Updated error handling to extract backend detail
      setError(
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        'Failed to change password'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="sm" 
      fullWidth
      disableEscapeKeyDown={isRequired && !success}
    >
      <DialogTitle>
        {isRequired ? 'Change Your Password' : 'Change Password'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {isRequired && !success && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              You are required to change your password before continuing.
            </Alert>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Password changed successfully!
              {isRequired && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  You can now continue using the application.
                </Typography>
              )}
            </Alert>
          )}

          {!success && (
            <form onSubmit={handleSubmit(onSubmit)}>
              <TextField
                fullWidth
                label="Current Password"
                type="password"
                margin="normal"
                {...register('currentPassword', {
                  required: 'Current password is required'
                })}
                error={!!errors.currentPassword}
                helperText={errors.currentPassword?.message}
                disabled={loading}
              />

              <TextField
                fullWidth
                label="New Password"
                type="password"
                margin="normal"
                {...register('newPassword', {
                  required: 'New password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters long'
                  },
                  pattern: {
                    value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/,
                    message: 'Password must contain at least one uppercase letter, one lowercase letter, and one number'
                  }
                })}
                error={!!errors.newPassword}
                helperText={errors.newPassword?.message}
                disabled={loading}
              />

              <TextField
                fullWidth
                label="Confirm New Password"
                type="password"
                margin="normal"
                {...register('confirmPassword', {
                  required: 'Please confirm your new password',
                  validate: (value) => {
                    if (value !== newPassword) {
                      return 'Passwords do not match';
                    }
                  }
                })}
                error={!!errors.confirmPassword}
                helperText={errors.confirmPassword?.message}
                disabled={loading}
              />

              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Password must be at least 8 characters long and contain at least one uppercase letter, 
                  one lowercase letter, and one number.
                </Typography>
              </Box>
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
            Change Password
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default PasswordChangeModal;