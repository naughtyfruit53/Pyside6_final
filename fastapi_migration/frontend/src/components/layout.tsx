import React from 'react';
import MegaMenu from './MegaMenu'; // Adjust path if needed
import { Box } from '@mui/material';

const Layout: React.FC<{ children: React.ReactNode; user?: any; onLogout: () => void }> = ({ children, user, onLogout }) => {
  return (
    <Box>
      <MegaMenu user={user} onLogout={onLogout} />
      <Box sx={{ mt: 2 }}> {/* Adjustable spacing below the menu */}
        {children}
      </Box>
    </Box>
  );
};

export default Layout;