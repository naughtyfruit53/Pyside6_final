import React, { useState } from 'react';
import { 
  Box, 
  Tab, 
  Tabs, 
  Typography, 
  Container,
  Alert,
  Button
} from '@mui/material';
import LoginForm from '../components/LoginForm';
import OTPLogin from '../components/OTPLogin';
import ForgotPasswordModal from '../components/ForgotPasswordModal';
import PasswordChangeModal from '../components/PasswordChangeModal';
import CompanyDetailsModal from '../components/CompanyDetailsModal';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`auth-tabpanel-${index}`}
      aria-labelledby={`auth-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const LoginPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);
  const [passwordChangeOpen, setPasswordChangeOpen] = useState(false);
  const [companyDetailsOpen, setCompanyDetailsOpen] = useState(false);
  const [requirePasswordChange, setRequirePasswordChange] = useState(false);
  const [requireCompanyDetails, setRequireCompanyDetails] = useState(false);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleLogin = (token: string, loginResponse?: any) => {
    // Store token
    localStorage.setItem('token', token);
    
    // Check if password change is required
    if (loginResponse?.must_change_password) {
      setRequirePasswordChange(true);
      setPasswordChangeOpen(true);
    }
    
    // Check if this is first login and company details are needed
    if (loginResponse?.is_first_login) {
      setRequireCompanyDetails(true);
      // If no password change required, show company details immediately
      if (!loginResponse?.must_change_password) {
        setCompanyDetailsOpen(true);
      }
    }
    
    // If no requirements, redirect directly to dashboard
    if (!loginResponse?.must_change_password && !loginResponse?.is_first_login) {
      window.location.href = '/dashboard';
    }
  };

  const handlePasswordChangeSuccess = () => {
    setPasswordChangeOpen(false);
    setRequirePasswordChange(false);
    
    // Check if company details are also required
    if (requireCompanyDetails) {
      setCompanyDetailsOpen(true);
    } else {
      // Redirect to dashboard
      window.location.href = '/dashboard';
    }
  };

  const handleCompanyDetailsSuccess = () => {
    setCompanyDetailsOpen(false);
    setRequireCompanyDetails(false);
    // Redirect to dashboard after successful company details entry
    window.location.href = '/dashboard';
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          TRITIQ ERP
        </Typography>
        <Typography variant="h6" component="h2" gutterBottom align="center" color="textSecondary">
          Enterprise Resource Planning System
        </Typography>

        <Alert severity="info" sx={{ mb: 3 }}>
          <strong>Demo Account:</strong> naughtyfruit53@gmail.com | Password: 123456<br/>
          <strong>OTP Login:</strong> Use the OTP tab for enhanced security authentication
        </Alert>

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="authentication tabs" centered>
            <Tab label="Standard Login" />
            <Tab label="OTP Authentication" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <LoginForm onLogin={handleLogin} />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <OTPLogin onLogin={handleLogin} />
        </TabPanel>

        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Button
            variant="text"
            color="primary"
            onClick={() => setForgotPasswordOpen(true)}
          >
            Forgot Password?
          </Button>
        </Box>
      </Box>

      {/* Forgot Password Modal */}
      <ForgotPasswordModal
        open={forgotPasswordOpen}
        onClose={() => setForgotPasswordOpen(false)}
        onSuccess={() => {
          setForgotPasswordOpen(false);
          // Show success message or redirect
        }}
      />

      {/* Password Change Modal (for required changes) */}
      <PasswordChangeModal
        open={passwordChangeOpen}
        onClose={() => setPasswordChangeOpen(false)}
        onSuccess={handlePasswordChangeSuccess}
        isRequired={requirePasswordChange}
      />

      {/* Company Details Modal (for first login) */}
      <CompanyDetailsModal
        open={companyDetailsOpen}
        onClose={() => setCompanyDetailsOpen(false)}
        onSuccess={handleCompanyDetailsSuccess}
        isRequired={requireCompanyDetails}
      />
    </Container>
  );
};

export default LoginPage;