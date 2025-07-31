// frontend/src/App.tsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// Import your pages, e.g., Login, Dashboard
import LoginPage from './pages/LoginPage'; // Adjust path as per your structure
import DashboardPage from './pages/DashboardPage'; // Adjust

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        {/* Add other routes */}
      </Routes>
    </Router>
  );
};

export default App;