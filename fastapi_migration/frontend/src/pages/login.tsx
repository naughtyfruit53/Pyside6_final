import React, { useState } from 'react';
import { 
  Box, 
  Tab, 
  Tabs, 
  Typography, 
  Container,
  Alert
} from '@mui/material';
import LoginForm from '../components/LoginForm';
import OTPLogin from '../components/OTPLogin';

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

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleLogin = (token: string) => {
    // Store token and redirect will be handled by components
    console.log('Login successful with token:', token);
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
      </Box>
    </Container>
  );
};

export default LoginPage;