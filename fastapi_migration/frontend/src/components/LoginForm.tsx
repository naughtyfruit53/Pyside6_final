import React, { useState, useRef, useEffect } from 'react';
import { 
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { useRouter } from 'next/router';
import { authService } from '../services/authService';

interface LoginFormProps {
  onLogin: (token: string, loginResponse?: any) => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const emailInputRef = useRef<HTMLInputElement>(null);
  
  const { register, handleSubmit, formState: { errors } } = useForm();
  const router = useRouter();

  // Auto-focus email field on component mount
  useEffect(() => {
    if (emailInputRef.current) {
      emailInputRef.current.focus();
    }
  }, []);

  const onSubmit = async (data: any) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await authService.loginWithEmail(data.email, data.password);
      
      // Store user info
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user_role', response.user_role);
      localStorage.setItem('organization_id', response.organization_id?.toString() || '');
      
      // Call parent callback with token and response
      onLogin(response.access_token, response);
    } catch (error: any) {
      // Better error handling to prevent flicker
      const errorMessage = error.message || error.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardContent sx={{ p: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom align="center">
          Standard Login
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address'
              }
            })}
            inputRef={emailInputRef}
            error={!!errors.email}
            helperText={errors.email?.message as string}
            margin="normal"
            autoFocus
            autoComplete="email"
          />

          <TextField
            fullWidth
            label="Password"
            type="password"
            {...register('password', {
              required: 'Password is required'
            })}
            error={!!errors.password}
            helperText={errors.password?.message as string}
            margin="normal"
            autoComplete="current-password"
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Login'}
          </Button>
        </Box>

        <Typography variant="body2" color="textSecondary" align="center">
          Use your email and password to login, or try OTP authentication for enhanced security.
        </Typography>
      </CardContent>
    </Card>
  );
};

export default LoginForm;