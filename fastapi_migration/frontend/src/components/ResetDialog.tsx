// ResetDialog component for requirement #2 - Add Reset Option for Superadmins
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  Checkbox,
  FormControlLabel,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';
import { toast } from 'react-toastify';

interface ResetDialogProps {
  open: boolean;
  onClose: () => void;
  resetType: 'organization' | 'entity';
  organizationName?: string;
  entityId?: number;
  onSuccess?: () => void;
}

const ResetDialog: React.FC<ResetDialogProps> = ({
  open,
  onClose,
  resetType,
  organizationName = '',
  entityId,
  onSuccess
}) => {
  const [confirmText, setConfirmText] = useState('');
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [loading, setLoading] = useState(false);

  const expectedConfirmText = resetType === 'organization' 
    ? 'RESET ORGANIZATION' 
    : 'RESET ENTITY';

  const handleReset = async () => {
    if (confirmText !== expectedConfirmText || !confirmChecked) {
      toast.error('Please confirm the reset action properly');
      return;
    }

    try {
      setLoading(true);
      
      const endpoint = resetType === 'organization' 
        ? '/api/v1/settings/reset/organization'
        : `/api/v1/settings/reset/entity`;

      const body = resetType === 'entity' && entityId
        ? { entity_id: entityId, confirm: true }
        : { confirm: true };

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
        throw new Error(error.detail || 'Reset failed');
      }

      const result = await response.json();
      toast.success(result.message || 'Reset completed successfully');
      
      if (onSuccess) {
        onSuccess();
      }
      
      handleClose();
    } catch (error) {
      console.error('Reset error:', error);
      toast.error(error instanceof Error ? error.message : 'Reset failed');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setConfirmText('');
    setConfirmChecked(false);
    setLoading(false);
    onClose();
  };

  const isConfirmValid = confirmText === expectedConfirmText && confirmChecked;

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <WarningIcon color="error" />
        {resetType === 'organization' ? 'Reset Organization Data' : 'Reset Entity Data'}
      </DialogTitle>
      
      <DialogContent>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            ⚠️ DANGER - This action cannot be undone!
          </Typography>
        </Alert>

        <Typography variant="body1" gutterBottom>
          {resetType === 'organization' 
            ? `This will permanently delete ALL data for the current organization${organizationName ? ` "${organizationName}"` : ''}.`
            : `This will permanently delete ALL data for the selected entity${organizationName ? ` "${organizationName}"` : ''}.`
          }
        </Typography>

        <Box sx={{ my: 2 }}>
          <Typography variant="body2" color="text.secondary">
            The following data will be deleted:
          </Typography>
          <ul>
            <li>All products and inventory</li>
            <li>All stock records</li>
            <li>All companies and customer/vendor data</li>
            <li>All vouchers and transactions</li>
            <li>All audit logs and notifications</li>
            <li>Non-admin user accounts</li>
          </ul>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Typography variant="body2" fontWeight="bold" gutterBottom>
          To confirm this action:
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" gutterBottom>
            1. Type "{expectedConfirmText}" in the box below:
          </Typography>
          <TextField
            fullWidth
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder={expectedConfirmText}
            disabled={loading}
            error={confirmText.length > 0 && confirmText !== expectedConfirmText}
            helperText={
              confirmText.length > 0 && confirmText !== expectedConfirmText
                ? `Must type exactly: ${expectedConfirmText}`
                : ''
            }
          />
        </Box>

        <FormControlLabel
          control={
            <Checkbox
              checked={confirmChecked}
              onChange={(e) => setConfirmChecked(e.target.checked)}
              disabled={loading}
            />
          }
          label="I understand this action is permanent and cannot be undone"
        />

        {resetType === 'organization' && (
          <Alert severity="info" sx={{ mt: 2 }}>
            The organization itself and admin user accounts will be preserved.
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
          onClick={handleReset}
          variant="contained"
          color="error"
          disabled={!isConfirmValid || loading}
          startIcon={loading ? <CircularProgress size={16} /> : null}
        >
          {loading ? 'Resetting...' : 'Reset Data'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ResetDialog;