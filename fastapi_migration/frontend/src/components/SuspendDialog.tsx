// SuspendDialog component for requirement #5 - Account Suspension & License Pause
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  TextField,
  Box,
  Alert,
  CircularProgress,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import { Block as BlockIcon, PlayArrow as ActivateIcon } from '@mui/icons-material';
import { toast } from 'react-toastify';

interface SuspendDialogProps {
  open: boolean;
  onClose: () => void;
  organizationId: number;
  organizationName: string;
  currentStatus: string;
  onSuccess?: () => void;
}

const SuspendDialog: React.FC<SuspendDialogProps> = ({
  open,
  onClose,
  organizationId,
  organizationName,
  currentStatus,
  onSuccess
}) => {
  const [reason, setReason] = useState('');
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [loading, setLoading] = useState(false);

  const isCurrentlySuspended = currentStatus === 'suspended';
  const action = isCurrentlySuspended ? 'activate' : 'suspend';

  const handleAction = async () => {
    if (!isCurrentlySuspended && !reason.trim()) {
      toast.error('Please provide a reason for suspension');
      return;
    }

    if (!confirmChecked) {
      toast.error('Please confirm the action');
      return;
    }

    try {
      setLoading(true);
      
      const endpoint = isCurrentlySuspended
        ? `/api/v1/settings/organization/${organizationId}/activate`
        : `/api/v1/settings/organization/${organizationId}/suspend`;

      const body = isCurrentlySuspended 
        ? {} 
        : { reason: reason.trim() };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to ${action} organization`);
      }

      const result = await response.json();
      toast.success(result.message || `Organization ${action}d successfully`);
      
      if (onSuccess) {
        onSuccess();
      }
      
      handleClose();
    } catch (error) {
      console.error(`${action} error:`, error);
      toast.error(error instanceof Error ? error.message : `Failed to ${action} organization`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setReason('');
    setConfirmChecked(false);
    setLoading(false);
    onClose();
  };

  const isValid = isCurrentlySuspended ? confirmChecked : (reason.trim().length > 0 && confirmChecked);

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {isCurrentlySuspended ? (
          <>
            <ActivateIcon color="success" />
            Activate Organization
          </>
        ) : (
          <>
            <BlockIcon color="error" />
            Suspend Organization
          </>
        )}
      </DialogTitle>
      
      <DialogContent>
        <Alert severity={isCurrentlySuspended ? "info" : "warning"} sx={{ mb: 2 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            {isCurrentlySuspended 
              ? 'Activate Organization Account'
              : '⚠️ Suspend Organization Account'
            }
          </Typography>
        </Alert>

        <Typography variant="body1" gutterBottom>
          {isCurrentlySuspended 
            ? `Are you sure you want to activate "${organizationName}"? This will restore full access to all users in this organization.`
            : `Are you sure you want to suspend "${organizationName}"? This will immediately block access for all users in this organization.`
          }
        </Typography>

        {!isCurrentlySuspended && (
          <Box sx={{ my: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Effects of suspension:
            </Typography>
            <ul>
              <li>All users will be logged out immediately</li>
              <li>Users cannot log in until reactivated</li>
              <li>Data is preserved but not accessible</li>
              <li>All API access is blocked</li>
            </ul>
          </Box>
        )}

        {!isCurrentlySuspended && (
          <Box sx={{ my: 2 }}>
            <TextField
              fullWidth
              label="Reason for Suspension"
              multiline
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={loading}
              placeholder="Enter the reason for suspending this organization..."
              required
            />
          </Box>
        )}

        <FormControlLabel
          control={
            <Checkbox
              checked={confirmChecked}
              onChange={(e) => setConfirmChecked(e.target.checked)}
              disabled={loading}
            />
          }
          label={isCurrentlySuspended 
            ? `I confirm that I want to activate "${organizationName}"`
            : `I confirm that I want to suspend "${organizationName}"`
          }
        />

        {!isCurrentlySuspended && (
          <Alert severity="error" sx={{ mt: 2 }}>
            This action takes effect immediately and will affect all users in the organization.
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button 
          onClick={handleClose} 
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          onClick={handleAction}
          variant="contained"
          color={isCurrentlySuspended ? "success" : "error"}
          disabled={!isValid || loading}
          startIcon={loading ? <CircularProgress size={16} /> : null}
        >
          {loading 
            ? `${isCurrentlySuspended ? 'Activating' : 'Suspending'}...`
            : `${isCurrentlySuspended ? 'Activate' : 'Suspend'} Organization`
          }
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SuspendDialog;