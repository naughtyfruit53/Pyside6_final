import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Tab, 
  Tabs, 
  Typography, 
  Container,
  Button
} from '@mui/material';
import LoginForm from '../components/LoginForm';
import OTPLogin from '../components/OTPLogin';
import ForgotPasswordModal from '../components/ForgotPasswordModal';
import PasswordChangeModal from '../components/PasswordChangeModal';
import CompanySetupModal from '../components/CompanySetupModal';
import { useCompany } from '../context/CompanyContext';

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
  const { checkCompanyDetails } = useCompany();
  const [tabValue, setTabValue] = useState(0);
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);
  const [passwordChangeOpen, setPasswordChangeOpen] = useState(false);
  const [requirePasswordChange, setRequirePasswordChange] = useState(false);

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
    } else {
      // Check company details immediately after login if no password change needed
      checkCompanyDetails().then(() => {
        window.location.href = '/dashboard';
      });
    }
  };

  const handlePasswordChangeSuccess = () => {
    setPasswordChangeOpen(false);
    setRequirePasswordChange(false);
    
    // Check company details after password change
    checkCompanyDetails().then(() => {
      window.location.href = '/dashboard';
    });
  };

  useEffect(() => {
    // Optional: Check on mount if already logged in
    if (localStorage.getItem('token')) {
      checkCompanyDetails();
    }
  }, []);

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          TRITIQ ERP
        </Typography>
        <Typography variant="h6" component="h2" gutterBottom align="center" color="textSecondary">
          Enterprise Resource Planning System
        </Typography>

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

      {/* Company Setup Modal */}
      <CompanySetupModal />
    </Container>
  );
};

export default LoginPage;