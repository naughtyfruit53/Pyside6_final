// Revised pages/MegaMenu.tsx

import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Menu,
  MenuItem,
  Box,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Avatar
} from '@mui/material';
import {
  Dashboard,
  Receipt,
  Inventory,
  People,
  Business,
  Assessment,
  Settings,
  AccountCircle,
  ExpandMore,
  ShoppingCart,
  LocalShipping,
  AccountBalance,
  SwapHoriz,
  TrendingUp,
  BarChart,
  Security,
  Storage,
  Build,
  ReceiptLong,
  NoteAdd,
  AddBusiness,
  DeveloperMode
} from '@mui/icons-material';
import { useRouter } from 'next/router';
import CreateOrganizationLicenseModal from './CreateOrganizationLicenseModal';

interface MegaMenuProps {
  user?: any;
  onLogout: () => void;
  isVisible?: boolean;
}

const MegaMenu: React.FC<MegaMenuProps> = ({ user, onLogout, isVisible = true }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [createLicenseModalOpen, setCreateLicenseModalOpen] = useState(false);
  const router = useRouter();

  // Add keyboard event listener for Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (anchorEl) {
          handleMenuClose();
        }
        if (userMenuAnchor) {
          handleUserMenuClose();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [anchorEl, userMenuAnchor]);

  // Don't render if not visible
  if (!isVisible) {
    return null;
  }

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, menuName: string) => {
    setAnchorEl(event.currentTarget);
    setActiveMenu(menuName);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setActiveMenu(null);
  };

  const handleUserMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const navigateTo = (path: string) => {
    router.push(path);
    handleMenuClose();
  };

  const handleCreateOrgLicense = () => {
    // For now, we'll use a state to control the modal
    // In a full implementation, this would be managed by parent component
    setCreateLicenseModalOpen(true);
    handleMenuClose();
  };

  const handleDemoMode = () => {
    // Enable demo mode - this could set a global state or localStorage flag
    localStorage.setItem('demoMode', 'true');
    // Optionally show a notification or redirect
    alert('Demo mode activated!');
    handleMenuClose();
  };

  // Check if user is superadmin
  const isSuperAdmin = user?.email === 'naughtyfruit53@gmail.com' || user?.is_super_admin;

  // Enhanced logo navigation function
  const navigateToHome = () => {
    router.push('/dashboard');
    handleMenuClose();
  };

  const menuItems = {
    vouchers: {
      title: 'Vouchers',
      icon: <Receipt />,
      sections: [
        {
          title: 'Purchase Vouchers',
          items: [
            { name: 'Purchase Order', path: '/vouchers/Purchase-Vouchers/purchase-order', icon: <LocalShipping /> },
            { name: 'GRN (Goods Received Note)', path: '/vouchers/Purchase-Vouchers/grn', icon: <Inventory /> },
            { name: 'Purchase Voucher', path: '/vouchers/Purchase-Vouchers/purchase-voucher', icon: <ShoppingCart /> },
            { name: 'Rejection In', path: '/vouchers/Purchase-Vouchers/rejection-in', icon: <SwapHoriz /> }
          ]
        },
        {
          title: 'Sales Vouchers',
          items: [
            { name: 'Sales Voucher', path: '/vouchers/Sales-Vouchers/sales-voucher', icon: <TrendingUp /> },
            { name: 'Delivery Challan', path: '/vouchers/Sales-Vouchers/delivery-challan', icon: <LocalShipping /> },
            { name: 'Non-Sales Credit Note', path: '/vouchers/Sales-Vouchers/non-sales-credit-note', icon: <AccountBalance /> },
            { name: 'Rejection Out', path: '/vouchers/Sales-Vouchers/rejection-out', icon: <SwapHoriz /> }
          ]
        },
        {
          title: 'Pre Sales Vouchers',
          items: [
            { name: 'Quotation', path: '/vouchers/Pre-Sales-Voucher/quotation', icon: <NoteAdd /> },
            { name: 'Proforma Invoice', path: '/vouchers/Pre-Sales-Voucher/proforma-invoice', icon: <ReceiptLong /> },
            { name: 'Sales Order', path: '/vouchers/Pre-Sales-Voucher/sales-order', icon: <Assessment /> }
          ]
        },
        {
          title: 'Financial Vouchers',
          items: [
            { name: 'Payment Voucher', path: '/vouchers/payment-voucher', icon: <AccountBalance /> },
            { name: 'Receipt Voucher', path: '/vouchers/receipt-voucher', icon: <AccountBalance /> },
            { name: 'Journal Voucher', path: '/vouchers/journal-voucher', icon: <AccountBalance /> },
            { name: 'Contra Voucher', path: '/vouchers/contra-voucher', icon: <AccountBalance /> },
            { name: 'Credit Note', path: '/vouchers/credit-note', icon: <AccountBalance /> },
            { name: 'Debit Note', path: '/vouchers/debit-note', icon: <AccountBalance /> }
          ]
        },
        {
          title: 'Internal Vouchers',
          items: [
            { name: 'Inter Department Voucher', path: '/vouchers/inter-department-voucher', icon: <SwapHoriz /> }
          ]
        }
      ]
    },
    masters: {
      title: 'Master Data',
      icon: <People />,
      sections: [
        {
          title: 'Business Partners',
          items: [
            { name: 'Vendors', path: '/masters/vendors', icon: <People /> },
            { name: 'Customers', path: '/masters/customers', icon: <Business /> },
            { name: 'Employees', path: '/masters/employees', icon: <People /> },
            { name: 'Company Details', path: '/masters/company-details', icon: <Business /> },
          ]
        },
        {
          title: 'Inventory',
          items: [
            { name: 'Products', path: '/masters/products', icon: <Inventory /> },
            { name: 'Categories', path: '/masters/categories', icon: <Storage /> },
            { name: 'Units', path: '/masters/units', icon: <Assessment /> }
          ]
        },
        {
          title: 'Financial',
          items: [
            { name: 'Chart of Accounts', path: '/masters/accounts', icon: <AccountBalance /> },
            { name: 'Tax Codes', path: '/masters/tax-codes', icon: <Assessment /> },
            { name: 'Payment Terms', path: '/masters/payment-terms', icon: <Business /> }
          ]
        }
      ]
    },
    inventory: {
      title: 'Inventory',
      icon: <Inventory />,
      sections: [
        {
          title: 'Stock Management',
          items: [
            { name: 'Current Stock', path: '/inventory/stock', icon: <Inventory /> },
            { name: 'Stock Movements', path: '/inventory/movements', icon: <SwapHoriz /> },
            { name: 'Low Stock Report', path: '/inventory/low-stock', icon: <TrendingUp /> }
          ]
        },
        {
          title: 'Warehouse',
          items: [
            { name: 'Locations', path: '/inventory/locations', icon: <Storage /> },
            { name: 'Bin Management', path: '/inventory/bins', icon: <Storage /> },
            { name: 'Cycle Count', path: '/inventory/cycle-count', icon: <Assessment /> }
          ]
        }
      ]
    },
    reports: {
      title: 'Reports',
      icon: <Assessment />,
      sections: [
        {
          title: 'Financial Reports',
          items: [
            { name: 'Trial Balance', path: '/reports/trial-balance', icon: <BarChart /> },
            { name: 'Profit & Loss', path: '/reports/profit-loss', icon: <TrendingUp /> },
            { name: 'Balance Sheet', path: '/reports/balance-sheet', icon: <Assessment /> }
          ]
        },
        {
          title: 'Inventory Reports',
          items: [
            { name: 'Stock Report', path: '/reports/stock', icon: <Inventory /> },
            { name: 'Valuation Report', path: '/reports/valuation', icon: <BarChart /> },
            { name: 'Movement Report', path: '/reports/movements', icon: <SwapHoriz /> }
          ]
        },
        {
          title: 'Business Reports',
          items: [
            { name: 'Sales Analysis', path: '/reports/sales-analysis', icon: <TrendingUp /> },
            { name: 'Purchase Analysis', path: '/reports/purchase-analysis', icon: <ShoppingCart /> },
            { name: 'Vendor Analysis', path: '/reports/vendor-analysis', icon: <People /> }
          ]
        }
      ]
    }
  };

  const renderMegaMenu = () => {
    if (!activeMenu || !menuItems[activeMenu as keyof typeof menuItems]) return null;

    const menu = menuItems[activeMenu as keyof typeof menuItems];

    return (
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            width: 800,
            maxHeight: 500,
            mt: 1
          }
        }}
        MenuListProps={{
          sx: { p: 2 }
        }}
      >
        <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
          {menu.title}
        </Typography>
        <Grid container spacing={2}>
          {menu.sections.map((section, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold', color: 'text.secondary' }}>
                {section.title}
              </Typography>
              <List dense>
                {section.items.map((item, itemIndex) => (
                  <ListItem
                    key={itemIndex}
                    button
                    onClick={() => navigateTo(item.path)}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      '&:hover': {
                        backgroundColor: 'primary.light',
                        color: 'primary.contrastText'
                      }
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText primary={item.name} />
                  </ListItem>
                ))}
              </List>
              {index < menu.sections.length - 1 && <Divider sx={{ mt: 1 }} />}
            </Grid>
          ))}
        </Grid>
      </Menu>
    );
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          {/* Enhanced Logo Section */}
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              cursor: 'pointer',
              mr: 3,
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: 1
              },
              p: 1,
              borderRadius: 1,
              transition: 'background-color 0.2s'
            }}
            onClick={navigateToHome}
          >
            <Avatar sx={{ bgcolor: 'white', color: 'primary.main', mr: 1 }}>
              <Dashboard />
            </Avatar>
            <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
              TRITIQ ERP
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            {/* Ordered menu items: Master Data, Inventory, Vouchers, Reports, Settings */}
            {['masters', 'inventory', 'vouchers', 'reports'].map((key) => {
              const menu = menuItems[key as keyof typeof menuItems];
              return (
                <Button
                  key={key}
                  color="inherit"
                  startIcon={menu.icon}
                  endIcon={<ExpandMore />}
                  onClick={(e) => handleMenuClick(e, key)}
                  sx={{ mx: 1 }}
                >
                  {menu.title}
                </Button>
              );
            })}

            <Button
              color="inherit"
              startIcon={<Settings />}
              onClick={() => router.push('/settings')}
              sx={{ mx: 1 }}
            >
              Settings
            </Button>

            {/* Superadmin Menu Options */}
            {isSuperAdmin && (
              <>
                <Button
                  color="inherit"
                  startIcon={<Security />}
                  onClick={() => router.push('/admin/license-management')}
                  sx={{ mx: 1 }}
                >
                  License Management
                </Button>
                <Button
                  color="inherit"
                  startIcon={<DeveloperMode />}
                  onClick={handleDemoMode}
                  sx={{ mx: 1 }}
                >
                  Demo
                </Button>
              </>
            )}
          </Box>

          <IconButton
            color="inherit"
            onClick={handleUserMenuClick}
            sx={{ ml: 2 }}
          >
            <AccountCircle />
          </IconButton>
        </Toolbar>
      </AppBar>

      {renderMegaMenu()}

      <Menu
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={handleUserMenuClose}
      >
        <MenuItem onClick={handleUserMenuClose}>
          <Typography variant="body2">
            {user?.full_name || user?.email || 'User'}
          </Typography>
        </MenuItem>
        <MenuItem onClick={handleUserMenuClose}>
          <Typography variant="body2" color="textSecondary">
            Role: {user?.role || 'Standard User'}
          </Typography>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => router.push('/profile')}>
          Profile Settings
        </MenuItem>
        <MenuItem onClick={onLogout}>
          Logout
        </MenuItem>
      </Menu>

      {/* Organization License Creation Modal */}
      <CreateOrganizationLicenseModal
        open={createLicenseModalOpen}
        onClose={() => setCreateLicenseModalOpen(false)}
        onSuccess={(result) => {
          console.log('License created:', result);
          // You might want to show a success notification here
        }}
      />
    </>
  );
};

export default MegaMenu;