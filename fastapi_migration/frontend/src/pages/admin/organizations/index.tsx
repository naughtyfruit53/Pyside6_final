import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  TextField,
  Alert,
  CircularProgress,
  Tooltip
} from '@mui/material';
import {
  MoreVert,
  Add,
  Pause,
  PlayArrow,
  Block,
  Delete,
  RestartAlt,
  Business,
  Warning,
  CheckCircle,
  Email
} from '@mui/icons-material';
import { useRouter } from 'next/router';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';

interface Organization {
  id: number;
  name: string;
  subdomain: string;
  status: string;
  plan_type: string;
  max_users: number;
  primary_email: string;
  primary_phone: string;
  created_at: string;
  updated_at?: string;
}

const OrganizationsPage: React.FC = () => {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [actionDialog, setActionDialog] = useState(false);
  const [actionType, setActionType] = useState<'suspend' | 'pause' | 'reactivate' | 'delete' | 'reset' | null>(null);
  const [confirmationText, setConfirmationText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Get user info for authorization
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const userRole = typeof window !== 'undefined' ? localStorage.getItem('userRole') : null;
  const isSuperAdmin = userRole === 'super_admin';

  // Fetch organizations
  const { data: organizations, isLoading } = useQuery(
    'organizations',
    async () => {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.get(`${API_BASE_URL}/api/v1/organizations/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    },
    { enabled: !!token }
  );

  // Organization action mutations
  const orgActionMutation = useMutation(
    async ({ orgId, action, data }: { orgId: number; action: string; data?: any }) => {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      let endpoint = '';
      let method = 'POST';
      
      switch (action) {
        case 'suspend':
          endpoint = `/api/v1/settings/organization/${orgId}/suspend`;
          break;
        case 'reactivate':
          endpoint = `/api/v1/settings/organization/${orgId}/activate`;
          break;
        case 'delete':
          endpoint = `/api/v1/organizations/${orgId}`;
          method = 'DELETE';
          break;
        case 'reset':
          endpoint = `/api/v1/settings/reset/entity`;
          data = { entity_id: orgId, confirm: true };
          break;
        default:
          throw new Error('Invalid action');
      }

      const response = await axios({
        method,
        url: `${API_BASE_URL}${endpoint}`,
        data,
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    },
    {
      onSuccess: (data, variables) => {
        queryClient.invalidateQueries('organizations');
        setSuccess(`Organization ${variables.action} completed successfully`);
        setActionDialog(false);
        setSelectedOrg(null);
        setActionType(null);
        setConfirmationText('');
        
        // Send confirmation email for reset action
        if (variables.action === 'reset') {
          setSuccess('Organization reset completed. Confirmation email sent to organization admin.');
        }
      },
      onError: (error: any) => {
        setError(error.response?.data?.detail || `Failed to ${actionType} organization`);
      }
    }
  );

  const handleContextMenu = (event: React.MouseEvent<HTMLButtonElement>, org: Organization) => {
    event.preventDefault();
    setAnchorEl(event.currentTarget);
    setSelectedOrg(org);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setSelectedOrg(null);
  };

  const handleAction = (action: 'suspend' | 'pause' | 'reactivate' | 'delete' | 'reset') => {
    setActionType(action);
    setActionDialog(true);
    handleCloseMenu();
  };

  const confirmAction = () => {
    if (!selectedOrg || !actionType) return;

    // For reset action, require confirmation text
    if (actionType === 'reset' && confirmationText !== 'RESET') {
      setError('Please type "RESET" to confirm this action');
      return;
    }

    // For delete action, require confirmation text
    if (actionType === 'delete' && confirmationText !== selectedOrg.name) {
      setError(`Please type "${selectedOrg.name}" to confirm deletion`);
      return;
    }

    const actionData: any = {};
    if (actionType === 'suspend') {
      actionData.reason = 'Administrative action';
    }

    orgActionMutation.mutate({
      orgId: selectedOrg.id,
      action: actionType,
      data: actionData
    });
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'success';
      case 'suspended': return 'error';
      case 'trial': return 'warning';
      case 'expired': return 'default';
      default: return 'default';
    }
  };

  const getActionAvailability = (org: Organization) => {
    const status = org.status.toLowerCase();
    return {
      suspend: status === 'active',
      reactivate: status === 'suspended' || status === 'expired',
      delete: true,
      reset: true
    };
  };

  // Check authorization
  if (!isSuperAdmin) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">
          You don't have permission to manage organizations. Only platform super administrators can access this page.
        </Alert>
        <Button onClick={() => router.push('/settings')} sx={{ mt: 2 }}>
          Back to Settings
        </Button>
      </Container>
    );
  }

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Organizations Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => router.push('/admin/organizations/create')}
        >
          Add Organization
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Organization</TableCell>
              <TableCell>Subdomain</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Plan</TableCell>
              <TableCell>Users</TableCell>
              <TableCell>Contact</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {organizations?.map((org: Organization) => (
              <TableRow key={org.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Business sx={{ mr: 1, color: 'primary.main' }} />
                    <Box>
                      <Typography variant="subtitle2">{org.name}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        ID: {org.id}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="primary">
                    {org.subdomain}.example.com
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={org.status}
                    color={getStatusColor(org.status) as any}
                    size="small"
                    icon={org.status === 'active' ? <CheckCircle /> : <Warning />}
                  />
                </TableCell>
                <TableCell>
                  <Chip label={org.plan_type} variant="outlined" size="small" />
                </TableCell>
                <TableCell>{org.max_users}</TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2">{org.primary_email}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {org.primary_phone}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {new Date(org.created_at).toLocaleDateString()}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Organization Actions">
                    <IconButton
                      onClick={(e) => handleContextMenu(e, org)}
                      size="small"
                    >
                      <MoreVert />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        {selectedOrg && (
          <>
            {getActionAvailability(selectedOrg).suspend && (
              <MenuItem onClick={() => handleAction('suspend')}>
                <Block sx={{ mr: 1 }} fontSize="small" />
                Suspend
              </MenuItem>
            )}
            {getActionAvailability(selectedOrg).reactivate && (
              <MenuItem onClick={() => handleAction('reactivate')}>
                <PlayArrow sx={{ mr: 1 }} fontSize="small" />
                Reactivate
              </MenuItem>
            )}
            <MenuItem onClick={() => handleAction('reset')}>
              <RestartAlt sx={{ mr: 1 }} fontSize="small" />
              Reset Data
            </MenuItem>
            <MenuItem onClick={() => handleAction('delete')} sx={{ color: 'error.main' }}>
              <Delete sx={{ mr: 1 }} fontSize="small" />
              Delete
            </MenuItem>
          </>
        )}
      </Menu>

      {/* Action Confirmation Dialog */}
      <Dialog open={actionDialog} onClose={() => setActionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <Warning sx={{ mr: 1, color: 'warning.main' }} />
          Confirm {actionType?.charAt(0).toUpperCase()}{actionType?.slice(1)} Organization
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to {actionType} the organization "{selectedOrg?.name}"?
          </DialogContentText>
          
          {actionType === 'reset' && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="error" sx={{ mb: 2 }}>
                This will permanently delete ALL data for this organization and send a confirmation email to the organization admin.
              </Alert>
              <TextField
                fullWidth
                label="Type 'RESET' to confirm"
                value={confirmationText}
                onChange={(e) => setConfirmationText(e.target.value)}
                placeholder="RESET"
              />
            </Box>
          )}

          {actionType === 'delete' && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="error" sx={{ mb: 2 }}>
                This will permanently delete the organization and all its data. This action cannot be undone.
              </Alert>
              <TextField
                fullWidth
                label={`Type "${selectedOrg?.name}" to confirm deletion`}
                value={confirmationText}
                onChange={(e) => setConfirmationText(e.target.value)}
                placeholder={selectedOrg?.name}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialog(false)}>Cancel</Button>
          <Button
            onClick={confirmAction}
            color={actionType === 'delete' || actionType === 'reset' ? 'error' : 'primary'}
            variant="contained"
            disabled={orgActionMutation.isLoading}
            startIcon={orgActionMutation.isLoading ? <CircularProgress size={16} /> : undefined}
          >
            {orgActionMutation.isLoading ? 'Processing...' : `${actionType?.charAt(0).toUpperCase()}${actionType?.slice(1)}`}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OrganizationsPage;