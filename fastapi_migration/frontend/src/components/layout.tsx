import React from 'react';
import MegaMenu from './MegaMenu'; // Adjust path if needed
import { Box } from '@mui/material';

const Layout: React.FC<{ 
  children: React.ReactNode; 
  user?: any; 
  onLogout: () => void;
  showMegaMenu?: boolean;
}> = ({ children, user, onLogout, showMegaMenu = true }) => {
  return (
    <Box>
      <MegaMenu user={user} onLogout={onLogout} isVisible={showMegaMenu} />
      <Box sx={{ mt: showMegaMenu ? 2 : 0 }}> {/* Adjustable spacing below the menu */}
        {children}
      </Box>
    </Box>
  );
};

export default Layout;