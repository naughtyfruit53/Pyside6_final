// Revised pages/dashboard.tsx

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
import { voucherService, masterDataService, companyService } from '../services/authService'; // Added companyService import
import { useQuery } from 'react-query';
import CompanyDetailsModal from '../components/CompanyDetailsModal';

export default function Dashboard() {
  const router = useRouter();
  const [showCompanyModal, setShowCompanyModal] = useState<boolean>(false);

  const { data: purchaseVouchers } = useQuery('purchaseVouchers', () =>
    voucherService.getVouchers('purchase', { limit: 5 })
  );

  const { data: salesVouchers } = useQuery('salesVouchers', () =>
    voucherService.getVouchers('sales', { limit: 5 })
  );

  const { data: lowStock } = useQuery('lowStock', () =>
    masterDataService.getLowStock()
  );

  const { data: company, isError, error } = useQuery('company', () =>
    companyService.getCurrentCompany(), // Fixed: Use companyService.getCurrentCompany()
    { retry: false }
  );

  useEffect(() => {
    // Check if company details are marked as incomplete in localStorage
    const companyDetailsCompleted = localStorage.getItem('companyDetailsCompleted');
    if (companyDetailsCompleted === 'false') {
      setShowCompanyModal(true);
    }
  }, []);

  const handleModalClose = () => {
    // Allow dismissing the modal, but it will reappear on next login
    setShowCompanyModal(false);
  };

  const handleModalSuccess = () => {
    // Mark as completed in localStorage and hide modal
    localStorage.setItem('companyDetailsCompleted', 'true');
    setShowCompanyModal(false);
    // Refetch company data
    window.location.reload(); // Simple refresh to update all data
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
      value: '1', // Assume active; adjust if needed based on global user state
      icon: <People />,
      color: '#7B1FA2'
    }
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
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
      </Container>
      <CompanyDetailsModal
        open={showCompanyModal}
        onClose={handleModalClose}
        onSuccess={handleModalSuccess}
        isRequired={true}
      />
    </Box>
  );
}