import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  AppBar,
  Toolbar,
  IconButton,
  Menu,
  MenuItem,
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import {
  AccountCircle,
  Dashboard as DashboardIcon,
  Receipt,
  Inventory,
  People,
  Business,
  Email,
  Warning
} from '@mui/icons-material';
import { useRouter } from 'next/router';
import { authService, voucherService, masterDataService } from '../services/authService';
import { useQuery } from 'react-query';
import { toast } from 'react-toastify';

export default function Dashboard() {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }

    // Get current user
    authService.getCurrentUser()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('token');
        router.push('/');
      });
  }, [router]);

  const { data: purchaseVouchers } = useQuery('purchaseVouchers', () =>
    voucherService.getPurchaseVouchers({ limit: 5 })
  );

  const { data: salesVouchers } = useQuery('salesVouchers', () =>
    voucherService.getSalesVouchers({ limit: 5 })
  );

  const { data: lowStock } = useQuery('lowStock', () =>
    masterDataService.getLowStock()
  );

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    authService.logout();
    handleClose();
  };

  const stats = [
    {
      title: 'Purchase Vouchers',
      value: purchaseVouchers?.length || 0,
      icon: <Receipt />,
      color: '#1976D2'
    },
    {
      title: 'Sales Vouchers',
      value: salesVouchers?.length || 0,
      icon: <Receipt />,
      color: '#2E7D32'
    },
    {
      title: 'Low Stock Items',
      value: lowStock?.length || 0,
      icon: <Warning />,
      color: '#F57C00'
    },
    {
      title: 'Active Session',
      value: user ? '1' : '0',
      icon: <People />,
      color: '#7B1FA2'
    }
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            TRITIQ ERP - Dashboard
          </Typography>
          {user && (
            <div>
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
              >
                <AccountCircle />
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem onClick={handleClose}>
                  Profile: {user.full_name || user.username}
                </MenuItem>
                <MenuItem onClick={handleClose}>
                  Role: {user.role}
                </MenuItem>
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </Menu>
            </div>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Grid container spacing={3}>
          {/* Statistics Cards */}
          {stats.map((stat, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ color: stat.color, mr: 2 }}>
                      {stat.icon}
                    </Box>
                    <Box>
                      <Typography color="textSecondary" gutterBottom>
                        {stat.title}
                      </Typography>
                      <Typography variant="h4" component="h2">
                        {stat.value}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}

          {/* Recent Purchase Vouchers */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Recent Purchase Vouchers
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Voucher #</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {purchaseVouchers?.slice(0, 5).map((voucher: any) => (
                      <TableRow key={voucher.id}>
                        <TableCell>{voucher.voucher_number}</TableCell>
                        <TableCell>
                          {new Date(voucher.date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>₹{voucher.total_amount?.toFixed(2)}</TableCell>
                        <TableCell>
                          <Chip
                            label={voucher.status}
                            color={voucher.status === 'confirmed' ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          {/* Recent Sales Vouchers */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Recent Sales Vouchers
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Voucher #</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {salesVouchers?.slice(0, 5).map((voucher: any) => (
                      <TableRow key={voucher.id}>
                        <TableCell>{voucher.voucher_number}</TableCell>
                        <TableCell>
                          {new Date(voucher.date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>₹{voucher.total_amount?.toFixed(2)}</TableCell>
                        <TableCell>
                          <Chip
                            label={voucher.status}
                            color={voucher.status === 'confirmed' ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          {/* Action Buttons */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item>
                  <Button
                    variant="contained"
                    startIcon={<Receipt />}
                    onClick={() => toast.info('Purchase voucher creation would open here')}
                  >
                    Create Purchase Voucher
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<Receipt />}
                    onClick={() => toast.info('Sales voucher creation would open here')}
                  >
                    Create Sales Voucher
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    startIcon={<People />}
                    onClick={() => toast.info('Vendor management would open here')}
                  >
                    Manage Vendors
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    startIcon={<Business />}
                    onClick={() => toast.info('Customer management would open here')}
                  >
                    Manage Customers
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    startIcon={<Inventory />}
                    onClick={() => toast.info('Stock management would open here')}
                  >
                    Stock Management
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>

        {/* Welcome Message */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="h5" color="primary" gutterBottom>
            Welcome to the FastAPI Migration of TRITIQ ERP!
          </Typography>
          <Typography variant="body1" color="textSecondary">
            ✅ Email-based authentication implemented<br/>
            ✅ Individual voucher tables created<br/>
            ✅ Email notification system ready<br/>
            ✅ RESTful API with comprehensive endpoints<br/>
            ✅ Modern web interface replacing PySide6
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}