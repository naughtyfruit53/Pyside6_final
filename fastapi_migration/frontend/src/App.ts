// frontend/src/App.tsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// Import your pages, e.g., Login, Dashboard
import LoginPage from './pages/LoginPage'; // Adjust path as per your structure
import DashboardPage from './pages/DashboardPage'; // Adjust
import { CompanyProvider, useCompany } from './context/CompanyContext';
import CompanySetupModal from './components/CompanySetupModal';

const AppContent: React.FC = () => {
  const { isCompanySetupNeeded, checkCompanyDetails } = useCompany();

  React.useEffect(() => {
    // Check company details on app startup or after login (call after successful login)
    checkCompanyDetails();
  }, []);

  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        {/* Add other routes */}
      </Routes>
      {isCompanySetupNeeded && <CompanySetupModal />}
    </>
  );
};

const App: React.FC = () => {
  return (
    <CompanyProvider>
      <Router>
        <AppContent />
      </Router>
    </CompanyProvider>
  );
};

export default App;