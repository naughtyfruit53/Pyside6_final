import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  FormGroup,
  Alert,
  CircularProgress,
  Divider,
  IconButton
} from '@mui/material';
import { ArrowBack, Person, Save, Cancel } from '@mui/icons-material';
import { useRouter } from 'next/router';
import { useMutation } from 'react-query';
import axios from 'axios';

const AddUser: React.FC = () => {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    role: 'standard_user',
    department: '',
    designation: '',
    employee_id: '',
    phone: ''
  });

  // Get user info for authorization
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const userRole = typeof window !== 'undefined' ? localStorage.getItem('userRole') : null;
  const canAddUser = userRole === 'org_admin' || userRole === 'super_admin';

  const createUserMutation = useMutation(
    async (userData: any) => {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/users/`,
        userData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    },
    {
      onSuccess: (data) => {
        setSuccess('User created successfully!');
        setError(null);
        // Redirect to user management after 2 seconds
        setTimeout(() => {
          router.push('/settings/user-management');
        }, 2000);
      },
      onError: (error: any) => {
        setError(error.response?.data?.detail || 'Failed to create user');
        setSuccess(null);
      }
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Basic validation
    if (!formData.email || !formData.username || !formData.full_name || !formData.password) {
      setError('Please fill in all required fields');
      return;
    }

    // Password validation
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    createUserMutation.mutate(formData);
  };

  const handleInputChange = (field: string) => (e: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  const resetForm = () => {
    setFormData({
      email: '',
      username: '',
      full_name: '',
      password: '',
      role: 'standard_user',
      department: '',
      designation: '',
      employee_id: '',
      phone: ''
    });
    setError(null);
    setSuccess(null);
  };

  // Check authorization
  if (!canAddUser) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">
          You don't have permission to add users. Only organization administrators can add users.
        </Alert>
        <Button 
          startIcon={<ArrowBack />} 
          onClick={() => router.push('/settings')}
          sx={{ mt: 2 }}
        >
          Back to Settings
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => router.push('/settings')} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" component="h1">
          Add New User
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ p: 4 }}>
        <form onSubmit={handleSubmit}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <Person sx={{ mr: 1 }} />
            User Information
          </Typography>
          <Divider sx={{ mb: 3 }} />

          {/* Basic Information */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
            <TextField
              fullWidth
              label="Email *"
              type="email"
              value={formData.email}
              onChange={handleInputChange('email')}
              required
              helperText="User's login email address"
            />
            <TextField
              fullWidth
              label="Username *"
              value={formData.username}
              onChange={handleInputChange('username')}
              required
              helperText="Unique username for login"
            />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
            <TextField
              fullWidth
              label="Full Name *"
              value={formData.full_name}
              onChange={handleInputChange('full_name')}
              required
            />
            <TextField
              fullWidth
              label="Password *"
              type="password"
              value={formData.password}
              onChange={handleInputChange('password')}
              required
              helperText="Minimum 8 characters"
            />
          </Box>

          {/* Role and Department */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Role *</InputLabel>
              <Select
                value={formData.role}
                label="Role *"
                onChange={handleInputChange('role')}
              >
                <MenuItem value="standard_user">Standard User</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
                {userRole === 'super_admin' && (
                  <MenuItem value="org_admin">Organization Admin</MenuItem>
                )}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Department"
              value={formData.department}
              onChange={handleInputChange('department')}
            />
          </Box>

          {/* Additional Information */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
            <TextField
              fullWidth
              label="Designation"
              value={formData.designation}
              onChange={handleInputChange('designation')}
            />
            <TextField
              fullWidth
              label="Employee ID"
              value={formData.employee_id}
              onChange={handleInputChange('employee_id')}
            />
          </Box>

          <TextField
            fullWidth
            label="Phone"
            value={formData.phone}
            onChange={handleInputChange('phone')}
            sx={{ mb: 4 }}
          />

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              startIcon={<Cancel />}
              onClick={() => router.push('/settings')}
              disabled={createUserMutation.isLoading}
            >
              Cancel
            </Button>
            <Button
              variant="outlined"
              onClick={resetForm}
              disabled={createUserMutation.isLoading}
            >
              Reset
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={createUserMutation.isLoading ? <CircularProgress size={20} /> : <Save />}
              disabled={createUserMutation.isLoading}
            >
              {createUserMutation.isLoading ? 'Creating...' : 'Create User'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Container>
  );
};

export default AddUser;