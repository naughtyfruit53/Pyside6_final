import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
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
  Receipt,
  Inventory,
  People,
  Business,
  Warning
} from '@mui/icons-material';
import { useRouter } from 'next/router';
import { authService, voucherService, masterDataService } from '../services/authService';
import { useQuery } from 'react-query';
import MegaMenu from '../components/MegaMenu';

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Get current user
    authService.getCurrentUser()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('token');
        router.push('/login');
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

  const handleLogout = () => {
    authService.logout();
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
      <MegaMenu user={user} onLogout={handleLogout} />

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
                    onClick={() => router.push('/vouchers/purchase')}
                  >
                    Create Purchase Voucher
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<Receipt />}
                    onClick={() => router.push('/vouchers/sales')}
                  >
                    Create Sales Voucher
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    startIcon={<People />}
                    onClick={() => router.push('/masters/vendors')}
                  >
                    Manage Vendors
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    startIcon={<Business />}
                    onClick={() => router.push('/masters/customers')}
                  >
                    Manage Customers
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    startIcon={<Inventory />}
                    onClick={() => router.push('/inventory/stock')}
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
            Welcome to the Enhanced TRITIQ ERP!
          </Typography>
          <Typography variant="body1" color="textSecondary">
            ✅ OTP-based authentication implemented<br/>
            ✅ Comprehensive mega menu navigation<br/>
            ✅ Organized voucher management system<br/>
            ✅ Master data management modules<br/>
            ✅ Inventory tracking and reporting<br/>
            ✅ Modern responsive web interface
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}