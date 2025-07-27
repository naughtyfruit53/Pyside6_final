import React, { useState } from 'react';
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
  IconButton
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
  Build
} from '@mui/icons-material';
import { useRouter } from 'next/router';

interface MegaMenuProps {
  user?: any;
  onLogout: () => void;
}

const MegaMenu: React.FC<MegaMenuProps> = ({ user, onLogout }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const router = useRouter();

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

  const menuItems = {
    vouchers: {
      title: 'Vouchers',
      icon: <Receipt />,
      sections: [
        {
          title: 'Purchase Vouchers',
          items: [
            { name: 'Purchase Voucher', path: '/vouchers/purchase', icon: <ShoppingCart /> },
            { name: 'Purchase Order', path: '/vouchers/purchase-order', icon: <LocalShipping /> },
            { name: 'Purchase Return', path: '/vouchers/purchase-return', icon: <SwapHoriz /> }
          ]
        },
        {
          title: 'Sales Vouchers',
          items: [
            { name: 'Sales Voucher', path: '/vouchers/sales', icon: <TrendingUp /> },
            { name: 'Sales Order', path: '/vouchers/sales-order', icon: <Assessment /> },
            { name: 'Sales Return', path: '/vouchers/sales-return', icon: <SwapHoriz /> }
          ]
        },
        {
          title: 'Financial Vouchers',
          items: [
            { name: 'Payment Voucher', path: '/vouchers/payment', icon: <AccountBalance /> },
            { name: 'Receipt Voucher', path: '/vouchers/receipt', icon: <AccountBalance /> },
            { name: 'Journal Voucher', path: '/vouchers/journal', icon: <AccountBalance /> },
            { name: 'Contra Voucher', path: '/vouchers/contra', icon: <AccountBalance /> }
          ]
        },
        {
          title: 'Internal Vouchers',
          items: [
            { name: 'Material Transfer', path: '/vouchers/material-transfer', icon: <SwapHoriz /> },
            { name: 'Stock Adjustment', path: '/vouchers/stock-adjustment', icon: <Inventory /> },
            { name: 'Production Voucher', path: '/vouchers/production', icon: <Build /> }
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
            { name: 'Employees', path: '/masters/employees', icon: <People /> }
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
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => router.push('/dashboard')}
            sx={{ mr: 2 }}
          >
            <Dashboard />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            TRITIQ ERP
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {Object.entries(menuItems).map(([key, menu]) => (
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
            ))}

            <Button
              color="inherit"
              startIcon={<Settings />}
              onClick={() => router.push('/settings')}
              sx={{ mx: 1 }}
            >
              Settings
            </Button>

            <IconButton
              color="inherit"
              onClick={handleUserMenuClick}
              sx={{ ml: 2 }}
            >
              <AccountCircle />
            </IconButton>
          </Box>
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
    </>
  );
};

export default MegaMenu;