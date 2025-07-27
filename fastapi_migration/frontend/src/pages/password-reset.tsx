// fastapi_migration/frontend/src/pages/password-reset.tsx

import React from 'react';
import { useForm } from 'react-hook-form';
import { Button, TextField } from '@mui/material';
import api from '../utils/api';
import { useRouter } from 'next/router';

const PasswordResetPage: React.FC = () => {
  const { register, handleSubmit } = useForm();
  const router = useRouter();

  const onSubmit = async (data: any) => {
    try {
      await api.post('/auth/reset-password', data);
      router.push('/login');
    } catch (error) {
      console.error('Password reset failed', error);
    }
  };

  return (
    <div>
      <h1>Reset Password</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <TextField label="New Password" type="password" {...register('new_password', { required: true })} fullWidth margin="normal" />
        <Button type="submit" variant="contained" color="primary">
          Reset
        </Button>
      </form>
    </div>
  );
};

export default PasswordResetPage;