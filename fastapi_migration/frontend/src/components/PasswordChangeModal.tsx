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
import { getFeatureFlag } from '../utils/config';

interface PasswordChangeModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  isRequired?: boolean; // For mandatory password changes
}

interface PasswordFormData {
  current_password?: string;
  new_password: string;
  confirm_password: string;
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
  
  // Check if password change functionality is enabled
  const passwordChangeEnabled = getFeatureFlag('passwordChange');
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    getValues
  } = useForm<PasswordFormData>();

  const new_password = watch('new_password');

  const handleClose = () => {
    if (!isRequired || success) {
      reset();
      setError(null);
      setSuccess(false);
      onClose();
    }
  };

  const onSubmit = async (data: PasswordFormData) => {
    console.log('🚀 PasswordChangeModal.onSubmit called');
    console.log('📝 Form data received:', {
      hasNewPassword: !!data.new_password,
      hasConfirmPassword: !!data.confirm_password,
      hasCurrentPassword: !!data.current_password,
      isRequired: isRequired,
      passwordsMatch: data.new_password === data.confirm_password
    });
    
    // Validation checks with detailed logging
    if (!data.new_password || !data.confirm_password) {
      const missingFields = [];
      if (!data.new_password) missingFields.push('new_password');
      if (!data.confirm_password) missingFields.push('confirm_password');
      
      console.error('❌ Validation failed - missing required fields:', missingFields);
      setError('New password and confirmation are required');
      return;
    }

    if (data.new_password !== data.confirm_password) {
      console.error('❌ Validation failed - passwords do not match');
      setError('New passwords do not match');
      return;
    }

    if (!isRequired && !data.current_password) {
      console.error('❌ Validation failed - current password required for normal password change');
      setError('Current password is required');
      return;
    }

    console.log('✅ Validation passed, proceeding with password change request');
    setLoading(true);
    setError(null);

    try {
      console.log('🔄 Calling passwordService.changePassword with parameters:', {
        currentPassword: isRequired ? 'null (mandatory change)' : 'provided',
        newPassword: 'provided',
        confirmPassword: 'provided',
        isRequired: isRequired
      });
      
      await passwordService.changePassword(
        isRequired ? null : data.current_password, 
        data.new_password,
        data.confirm_password  // Always send confirm_password now
      );
      
      console.log('🎉 Password change successful!');
      setSuccess(true);
      
      if (onSuccess) {
        console.log('📞 Calling onSuccess callback');
        onSuccess();
      }
      
      if (!isRequired) {
        console.log('⏰ Setting auto-close timer for non-mandatory change');
        setTimeout(() => {
          handleClose();
        }, 2000);
      } else {
        console.log('✋ Not auto-closing due to mandatory change requirement');
      }
    } catch (err: any) {
      // Enhanced error handling to extract backend detail and handle objects/arrays
      let errorMessage = 'Failed to change password';
      
      // Log the full error for debugging
      console.error('💥 Password change error details:', {
        error: err,
        response: err.response?.data,
        status: err.response?.status,
        message: err.message
      });
      
      // Try to extract from various error structures
      const detail = err.response?.data?.detail;
      const message = err.response?.data?.message;
      
      if (typeof detail === 'string' && detail) {
        errorMessage = detail;
        console.log('📋 Using detail from response:', detail);
      } else if (typeof message === 'string' && message) {
        errorMessage = message;
        console.log('📋 Using message from response:', message);
      } else if (Array.isArray(detail) && detail.length > 0) {
        // Handle Pydantic validation errors
        const messages = detail.map(e => e.msg || `${e.loc?.join(' -> ')}: ${e.type}`).filter(Boolean);
        errorMessage = messages.length > 0 ? messages.join(', ') : 'Validation error';
        console.log('📋 Using Pydantic validation errors:', messages);
      } else if (detail && typeof detail === 'object') {
        // Handle object error details
        errorMessage = detail.error || detail.message || 'Invalid request format';
        console.log('📋 Using object detail:', detail);
      } else if (typeof err.message === 'string' && err.message && !err.message.includes('[object Object]')) {
        errorMessage = err.message;
        console.log('📋 Using error message:', err.message);
      } else if (err.status === 422) {
        errorMessage = 'Invalid request. Please check your input fields.';
        console.log('📋 Using default 422 error message');
      }
      
      console.error('🚨 Final error message for user:', errorMessage);
      setError(errorMessage);
    } finally {
      console.log('🔚 Password change request completed, setting loading to false');
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

          {!passwordChangeEnabled && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Password change functionality is temporarily disabled. Please contact your administrator.
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

          {!success && passwordChangeEnabled && (
            <form onSubmit={handleSubmit(onSubmit)}>
              {!isRequired && (
                <TextField
                  fullWidth
                  label="Current Password"
                  type="password"
                  margin="normal"
                  {...register('current_password', {
                    required: 'Current password is required'
                  })}
                  error={!!errors.current_password}
                  helperText={errors.current_password?.message}
                  disabled={loading}
                />
              )}

              <TextField
                fullWidth
                label="New Password"
                type="password"
                margin="normal"
                {...register('new_password', {
                  required: 'New password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters long'
                  },
                  pattern: {
                    value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&].+$/,
                    message: 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
                  }
                })}
                error={!!errors.new_password}
                helperText={errors.new_password?.message}
                disabled={loading}
              />

              <TextField
                fullWidth
                label="Confirm New Password"
                type="password"
                margin="normal"
                {...register('confirm_password', {
                  required: 'Please confirm your new password',
                  validate: (value) => {
                    if (value !== new_password) {
                      return 'Passwords do not match';
                    }
                  }
                })}
                error={!!errors.confirm_password}
                helperText={errors.confirm_password?.message}
                disabled={loading}
              />

              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Password must be at least 8 characters long and contain at least one uppercase letter, 
                  one lowercase letter, one number, and one special character (@$!%*?&).
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
        {!success && passwordChangeEnabled && (
          <Button
            onClick={() => {
              console.log('🖱️ Change Password button clicked');
              console.log('📊 Button state:', {
                loading: loading,
                disabled: loading,
                passwordChangeEnabled: passwordChangeEnabled,
                isRequired: isRequired,
                success: success
              });
              handleSubmit(onSubmit)();
            }}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            Change Password
          </Button>
        )}
        {!passwordChangeEnabled && (isRequired ? (
          <Button onClick={handleClose} variant="contained">
            Continue Without Changing Password
          </Button>
        ) : (
          <Button onClick={handleClose}>
            Close
          </Button>
        ))}
      </DialogActions>
    </Dialog>
  );
};

export default PasswordChangeModal;