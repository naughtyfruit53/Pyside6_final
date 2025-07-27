// fastapi_migration/frontend/src/components/LoginForm.tsx

import React from 'react';
import { useForm } from 'react-hook-form';
import { Button, TextField } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import { useRouter } from 'next/router';

const LoginForm: React.FC = () => {
  const { register, handleSubmit } = useForm();
  const { login } = useAuth();
  const router = useRouter();

  const onSubmit = async (data: any) => {
    try {
      const response = await authService.login(data.username, data.password);
      login(response.access_token);
      router.push('/admin');
    } catch (error) {
      console.error('Login failed', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <TextField label="Username" {...register('username', { required: true })} fullWidth margin="normal" />
      <TextField label="Password" type="password" {...register('password', { required: true })} fullWidth margin="normal" />
      <Button type="submit" variant="contained" color="primary">
        Login
      </Button>
    </form>
  );
};

export default LoginForm;