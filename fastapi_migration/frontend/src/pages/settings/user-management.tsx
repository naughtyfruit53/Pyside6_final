import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Alert,
  Divider
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Lock,
  LockOpen,
  RestartAlt,
  Visibility,
  Person,
  Security,
  AdminPanelSettings,
  Group
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useRouter } from 'next/router';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: string;
  department?: string;
  designation?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

const UserManagement: React.FC = () => {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'reset' | 'activate' | 'deactivate' | 'delete' | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    role: 'standard_user',
    department: '',
    designation: '',
    modules: {
      masters: false,
      inventory: false,
      vouchers: false,
      reports: false
    }
  });

  // Mock API calls - replace with actual service calls
  const { data: users, isLoading } = useQuery(
    'organization-users',
    async () => {
      // Replace with actual API call
      return [];
    }
  );

  const createUserMutation = useMutation(
    async (data: any) => {
      // Replace with actual API call
      console.log('Creating user:', data);
      return { message: 'User created successfully' };
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('organization-users');
        setCreateDialogOpen(false);
        resetForm();
      }
    }
  );

  const updateUserMutation = useMutation(
    async ({ userId, data }: { userId: number; data: any }) => {
      // Replace with actual API call
      console.log('Updating user:', userId, data);
      return { message: 'User updated successfully' };
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('organization-users');
        setEditDialogOpen(false);
        setSelectedUser(null);
        resetForm();
      }
    }
  );

  const userActionMutation = useMutation(
    async ({ userId, action }: { userId: number; action: string }) => {
      // Replace with actual API call
      console.log('User action:', userId, action);
      return { message: `User ${action} successfully` };
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('organization-users');
        setActionDialogOpen(false);
        setSelectedUser(null);
        setActionType(null);
      }
    }
  );

  const resetForm = () => {
    setFormData({
      email: '',
      username: '',
      full_name: '',
      password: '',
      role: 'standard_user',
      department: '',
      designation: '',
      modules: {
        masters: false,
        inventory: false,
        vouchers: false,
        reports: false
      }
    });
  };

  const handleCreateUser = () => {
    createUserMutation.mutate(formData);
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setFormData({
      email: user.email,
      username: user.username,
      full_name: user.full_name,
      password: '',
      role: user.role,
      department: user.department || '',
      designation: user.designation || '',
      modules: {
        masters: true, // These would come from user permissions
        inventory: true,
        vouchers: user.role === 'admin',
        reports: true
      }
    });
    setEditDialogOpen(true);
  };

  const handleUpdateUser = () => {
    if (selectedUser) {
      updateUserMutation.mutate({
        userId: selectedUser.id,
        data: formData
      });
    }
  };

  const handleAction = (user: User, action: 'reset' | 'activate' | 'deactivate' | 'delete') => {
    setSelectedUser(user);
    setActionType(action);
    setActionDialogOpen(true);
  };

  const confirmAction = () => {
    if (selectedUser && actionType) {
      userActionMutation.mutate({
        userId: selectedUser.id,
        action: actionType
      });
    }
  };

  const getRoleChip = (role: string) => {
    const roleConfig = {
      admin: { label: 'Admin', color: 'primary' as const },
      standard_user: { label: 'Standard User', color: 'default' as const },
      org_admin: { label: 'Organization Admin', color: 'secondary' as const }
    };
    
    const config = roleConfig[role as keyof typeof roleConfig] || 
                   { label: role, color: 'default' as const };
    
    return <Chip label={config.label} color={config.color} size="small" />;
  };

  const getStatusChip = (isActive: boolean) => {
    return (
      <Chip 
        label={isActive ? 'Active' : 'Inactive'} 
        color={isActive ? 'success' : 'error'} 
        size="small" 
      />
    );
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          User Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Add New User
        </Button>
      </Box>

      <Paper sx={{ mb: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <Group sx={{ mr: 1 }} />
          Users Overview
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {users?.length || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Total Users
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {users?.filter((user: User) => user.is_active).length || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Active Users
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {users?.filter((user: User) => user.role === 'admin').length || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Admin Users
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="secondary.main">
                {users?.filter((user: User) => user.role === 'standard_user').length || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Standard Users
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : users?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No users found. Add your first user to get started.
                </TableCell>
              </TableRow>
            ) : (
              users?.map((user: User) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Person sx={{ mr: 1, color: 'primary.main' }} />
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {user.full_name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          @{user.username}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {user.email}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {getRoleChip(user.role)}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {user.department || '-'}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {user.designation || ''}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {getStatusChip(user.is_active)}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => handleEditUser(user)}
                      title="Edit User"
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      size="small"
                      color="info"
                      onClick={() => handleAction(user, 'reset')}
                      title="Reset Password"
                    >
                      <RestartAlt />
                    </IconButton>
                    {user.is_active ? (
                      <IconButton
                        size="small"
                        color="warning"
                        onClick={() => handleAction(user, 'deactivate')}
                        title="Deactivate User"
                      >
                        <Lock />
                      </IconButton>
                    ) : (
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => handleAction(user, 'activate')}
                        title="Activate User"
                      >
                        <LockOpen />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleAction(user, 'delete')}
                      title="Delete User"
                    >
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create User Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New User</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={formData.full_name}
                onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Username"
                value={formData.username}
                onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={formData.role}
                  label="Role"
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                >
                  <MenuItem value="standard_user">Standard User</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Department"
                value={formData.department}
                onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Designation"
                value={formData.designation}
                onChange={(e) => setFormData(prev => ({ ...prev, designation: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Module Access
              </Typography>
              <FormGroup row>
                {Object.entries(formData.modules).map(([module, checked]) => (
                  <FormControlLabel
                    key={module}
                    control={
                      <Checkbox
                        checked={checked}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          modules: { ...prev.modules, [module]: e.target.checked }
                        }))}
                        disabled={formData.role === 'admin'} // Admin gets all modules
                      />
                    }
                    label={module.charAt(0).toUpperCase() + module.slice(1)}
                  />
                ))}
              </FormGroup>
              {formData.role === 'admin' && (
                <Typography variant="caption" color="textSecondary">
                  Admin users have access to all modules except user creation.
                </Typography>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateUser} 
            variant="contained"
            disabled={createUserMutation.isLoading}
          >
            {createUserMutation.isLoading ? 'Creating...' : 'Create User'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={formData.full_name}
                onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Username"
                value={formData.username}
                onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={formData.role}
                  label="Role"
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                >
                  <MenuItem value="standard_user">Standard User</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Department"
                value={formData.department}
                onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Designation"
                value={formData.designation}
                onChange={(e) => setFormData(prev => ({ ...prev, designation: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Module Access
              </Typography>
              <FormGroup row>
                {Object.entries(formData.modules).map(([module, checked]) => (
                  <FormControlLabel
                    key={module}
                    control={
                      <Checkbox
                        checked={checked}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          modules: { ...prev.modules, [module]: e.target.checked }
                        }))}
                        disabled={formData.role === 'admin'} // Admin gets all modules
                      />
                    }
                    label={module.charAt(0).toUpperCase() + module.slice(1)}
                  />
                ))}
              </FormGroup>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleUpdateUser} 
            variant="contained"
            disabled={updateUserMutation.isLoading}
          >
            {updateUserMutation.isLoading ? 'Updating...' : 'Update User'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Action Confirmation Dialog */}
      <Dialog open={actionDialogOpen} onClose={() => setActionDialogOpen(false)}>
        <DialogTitle>
          Confirm {actionType === 'reset' ? 'Password Reset' : 
                   actionType === 'activate' ? 'User Activation' : 
                   actionType === 'deactivate' ? 'User Deactivation' : 'User Deletion'}
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to {actionType} user 
            <strong> {selectedUser?.full_name}</strong>?
          </Typography>
          {actionType === 'reset' && (
            <Alert severity="info" sx={{ mt: 2 }}>
              A new temporary password will be generated and sent to the user's email.
            </Alert>
          )}
          {actionType === 'delete' && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              This action cannot be undone. The user will lose access permanently.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={confirmAction} 
            variant="contained"
            color={actionType === 'delete' ? 'error' : 'primary'}
            disabled={userActionMutation.isLoading}
          >
            {userActionMutation.isLoading ? 'Processing...' : 'Confirm'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UserManagement;