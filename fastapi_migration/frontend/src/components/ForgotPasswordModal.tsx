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
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { passwordService } from '../services/authService';

interface ForgotPasswordModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

interface ForgotPasswordFormData {
  email: string;
}

interface ResetPasswordFormData {
  otp: string;
  newPassword: string;
  confirmPassword: string;
}

const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({
  open,
  onClose,
  onSuccess
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(0);
  const [email, setEmail] = useState('');
  
  const {
    register: registerForgot,
    handleSubmit: handleSubmitForgot,
    formState: { errors: errorsForgot },
    reset: resetForgot
  } = useForm<ForgotPasswordFormData>();

  const {
    register: registerReset,
    handleSubmit: handleSubmitReset,
    formState: { errors: errorsReset },
    reset: resetReset,
    watch
  } = useForm<ResetPasswordFormData>();

  const newPassword = watch('newPassword');

  const handleClose = () => {
    resetForgot();
    resetReset();
    setError(null);
    setStep(0);
    setEmail('');
    onClose();
  };

  const onSubmitForgotPassword = async (data: ForgotPasswordFormData) => {
    setLoading(true);
    setError(null);

    try {
      await passwordService.forgotPassword(data.email);
      setEmail(data.email);
      setStep(1);
    } catch (err: any) {
      setError(err.message || 'Failed to send password reset email');
    } finally {
      setLoading(false);
    }
  };

  const onSubmitResetPassword = async (data: ResetPasswordFormData) => {
    setLoading(true);
    setError(null);

    try {
      await passwordService.resetPassword(email, data.otp, data.newPassword);
      setStep(2);
      if (onSuccess) {
        onSuccess();
      }
      setTimeout(() => {
        handleClose();
      }, 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  const steps = ['Request Reset', 'Verify & Reset', 'Complete'];

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Forgot Password</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <Stepper activeStep={step} sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {step === 0 && (
            <>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Enter your email address and we'll send you an OTP to reset your password.
              </Typography>
              <form onSubmit={handleSubmitForgot(onSubmitForgotPassword)}>
                <TextField
                  fullWidth
                  label="Email Address"
                  type="email"
                  margin="normal"
                  {...registerForgot('email', {
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Invalid email address'
                    }
                  })}
                  error={!!errorsForgot.email}
                  helperText={errorsForgot.email?.message}
                  disabled={loading}
                />
              </form>
            </>
          )}

          {step === 1 && (
            <>
              <Alert severity="info" sx={{ mb: 2 }}>
                An OTP has been sent to <strong>{email}</strong>. 
                Please check your email and enter the OTP below along with your new password.
              </Alert>
              <form onSubmit={handleSubmitReset(onSubmitResetPassword)}>
                <TextField
                  fullWidth
                  label="OTP Code"
                  margin="normal"
                  {...registerReset('otp', {
                    required: 'OTP is required',
                    pattern: {
                      value: /^\d{6}$/,
                      message: 'OTP must be 6 digits'
                    }
                  })}
                  error={!!errorsReset.otp}
                  helperText={errorsReset.otp?.message}
                  disabled={loading}
                />

                <TextField
                  fullWidth
                  label="New Password"
                  type="password"
                  margin="normal"
                  {...registerReset('newPassword', {
                    required: 'New password is required',
                    minLength: {
                      value: 8,
                      message: 'Password must be at least 8 characters long'
                    }
                  })}
                  error={!!errorsReset.newPassword}
                  helperText={errorsReset.newPassword?.message}
                  disabled={loading}
                />

                <TextField
                  fullWidth
                  label="Confirm New Password"
                  type="password"
                  margin="normal"
                  {...registerReset('confirmPassword', {
                    required: 'Please confirm your new password',
                    validate: (value) => {
                      if (value !== newPassword) {
                        return 'Passwords do not match';
                      }
                    }
                  })}
                  error={!!errorsReset.confirmPassword}
                  helperText={errorsReset.confirmPassword?.message}
                  disabled={loading}
                />
              </form>
            </>
          )}

          {step === 2 && (
            <Alert severity="success">
              <Typography variant="body1" gutterBottom>
                Password reset successfully!
              </Typography>
              <Typography variant="body2">
                You can now log in with your new password. This window will close automatically.
              </Typography>
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        {step < 2 && (
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
        )}
        {step === 0 && (
          <Button
            onClick={handleSubmitForgot(onSubmitForgotPassword)}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            Send OTP
          </Button>
        )}
        {step === 1 && (
          <>
            <Button
              onClick={() => setStep(0)}
              disabled={loading}
            >
              Back
            </Button>
            <Button
              onClick={handleSubmitReset(onSubmitResetPassword)}
              variant="contained"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : null}
            >
              Reset Password
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ForgotPasswordModal;