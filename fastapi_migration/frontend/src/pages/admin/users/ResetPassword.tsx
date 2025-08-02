import React, { useState } from 'react';
import { Box, Button, TextField, Typography, Dialog, DialogContent, DialogTitle, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import PushPinIcon from '@mui/icons-material/PushPin';
import { useForm } from 'react-hook-form';
import { organizationService } from '../../../services/authService';  // Replace with service for reset

interface ResetFormData {
  target_email: str;
}

const ResetPassword: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<ResetFormData>();
  const [popupOpen, setPopupOpen] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [resetEmail, setResetEmail] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const onSubmit = async (data: ResetFormData) => {
    try {
      const response = await organizationService.resetUserPassword(data.target_email);  // Adjust call
      setNewPassword(response.new_password);
      setResetEmail(response.target_email);
      setPopupOpen(true);
      setErrorMessage('');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to reset password');
    }
  };

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4">Reset User Password</Typography>
      <form onSubmit={handleSubmit(onSubmit)}>
        <TextField
          label="Target Email"
          {...register('target_email', { required: true })}
          error={!!errors.target_email}
          helperText={errors.target_email ? 'Email is required' : ''}
          fullWidth
          sx={{ mt: 2 }}
        />
        <Button type="submit" variant="contained" sx={{ mt: 2 }}>
          Reset Password
        </Button>
      </form>
      {errorMessage && <Typography color="error" sx={{ mt: 2 }}>{errorMessage}</Typography>}

      {/* Popup for temp password */}
      <Dialog open={popupOpen} onClose={() => setPopupOpen(false)}>
        <DialogTitle>Temporary Password</DialogTitle>
        <DialogContent>
          <Typography>New password for {resetEmail}: {newPassword}</Typography>
          <Typography variant="body2">Share this with the user and advise immediate change.</Typography>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default ResetPassword;