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
    console.log('🔐 Starting password change submission');
    console.log('📝 Form submission data:', {
      hasCurrentPassword: !!data.current_password,
      hasNewPassword: !!data.new_password,
      hasConfirmPassword: !!data.confirm_password,
      isRequiredChange: isRequired
    });
    
    // Client-side validation
    if (!data.new_password || !data.confirm_password) {
      console.error('❌ Validation failed: New password and confirmation are required');
      setError('New password and confirmation are required');
      return;
    }

    if (data.new_password !== data.confirm_password) {
      console.error('❌ Validation failed: New passwords do not match');
      setError('New passwords do not match');
      return;
    }

    if (!isRequired && !data.current_password) {
      console.error('❌ Validation failed: Current password is required for normal users');
      setError('Current password is required');
      return;
    }

    console.log('✅ Client-side validation passed');
    setLoading(true);
    setError(null);

    try {
      console.log(`🚀 Calling password service - isRequired: ${isRequired}`);
      await passwordService.changePassword(isRequired ? null : data.current_password, data.new_password);
      console.log('🎉 Password change successful!');
      setSuccess(true);
      if (onSuccess) {
        console.log('📞 Calling onSuccess callback');
        onSuccess();
      }
      if (!isRequired) {
        console.log('⏰ Auto-closing modal in 2 seconds');
        setTimeout(() => {
          handleClose();
        }, 2000);
      }
    } catch (err: any) {
      console.error('💥 Password change failed:', err);
      
      // Enhanced error handling to extract backend detail and handle objects/arrays
      let errorMessage = 'Failed to change password';
      
      // Log the full error structure for debugging
      console.error('🔍 Full error object:', err);
      console.error('🔍 Error response:', err.response);
      console.error('🔍 Error response data:', err.response?.data);
      
      // Try to extract from various error structures
      const detail = err.response?.data?.detail;
      const message = err.response?.data?.message;
      
      console.log('📊 Error analysis:', {
        hasDetail: !!detail,
        detailType: typeof detail,
        hasMessage: !!message,
        messageType: typeof message,
        statusCode: err.response?.status
      });
      
      if (typeof detail === 'string' && detail) {
        console.log('✅ Using string detail as error message');
        errorMessage = detail;
      } else if (typeof message === 'string' && message) {
        console.log('✅ Using string message as error message');
        errorMessage = message;
      } else if (Array.isArray(detail) && detail.length > 0) {
        console.log('🔄 Processing validation error array');
        // Handle Pydantic validation errors
        const messages = detail.map(e => e.msg || `${e.loc?.join(' -> ')}: ${e.type}`).filter(Boolean);
        errorMessage = messages.length > 0 ? messages.join(', ') : 'Validation error';
        console.log('📝 Processed validation messages:', messages);
      } else if (detail && typeof detail === 'object') {
        console.log('🔄 Processing object detail');
        // Handle object error details
        errorMessage = detail.error || detail.message || 'Invalid request format';
      } else if (typeof err.message === 'string' && err.message && !err.message.includes('[object Object]')) {
        console.log('✅ Using error.message as fallback');
        errorMessage = err.message;
      } else if (err.status === 422) {
        console.log('⚠️ Using default message for 422 error');
        errorMessage = 'Invalid request. Please check your input fields.';
      }
      
      console.error('❌ Final error message to display:', errorMessage);
      setError(errorMessage);
    } finally {
      console.log('🔄 Setting loading to false');
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
            onClick={(e) => {
              console.log('🖱️ Change Password button clicked');
              console.log('🔍 Button state:', { loading, success, passwordChangeEnabled });
              handleSubmit(onSubmit)(e);
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