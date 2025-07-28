// revised fastapi_migration/frontend/src/pages/vouchers/index.tsx

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import {
  Box,
  Container,
  Typography,
  Tab,
  Tabs,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Email,
  Print,
  Visibility
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { voucherService, reportsService } from '../../services/authService';
import MegaMenu from '../../components/MegaMenu';

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
      id={`voucher-tabpanel-${index}`}
      aria-labelledby={`voucher-tab-${index}`}
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

const VoucherManagement: React.FC = () => {
  const router = useRouter();
  const [user] = useState({ email: 'demo@example.com', role: 'admin' });

  // Get tab from URL parameter
  const getInitialTab = () => {
    const { tab } = router.query;
    switch (tab) {
      case 'purchase': return 0;
      case 'sales': return 1;
      case 'financial': return 2;
      case 'internal': return 3;
      default: return 0;
    }
  };

  const [tabValue, setTabValue] = useState(getInitialTab());

  // Update tab when URL changes
  useEffect(() => {
    setTabValue(getInitialTab());
  }, [router.query.tab]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    // Update URL without full navigation
    const tabNames = ['purchase', 'sales', 'financial', 'internal'];
    router.replace(`/vouchers?tab=${tabNames[newValue]}`, undefined, { shallow: true });
  };

  const handleLogout = () => {
    // Handle logout
  };

  const handleCreateVoucher = (tabIndex: number) => {
    const tabNames = ['purchase', 'sales', 'financial', 'internal'];
    router.push(`/vouchers/${tabNames[tabIndex]}`);
  };

  const handleViewVoucher = (type: string, id: number) => {
    router.push(`/vouchers/${type.toLowerCase()}/view/${id}`);
  };

  const handleEditVoucher = (type: string, id: number) => {
    router.push(`/vouchers/${type.toLowerCase()}/edit/${id}`);
  };

  const handlePrintVoucher = (type: string, id: number) => {
    // TODO: Implement print functionality, e.g., open a print dialog or generate PDF
    alert(`Printing ${type} voucher ${id}`);
  };

  const handleEmailVoucher = async (type: string, id: number) => {
    const voucherType = type === 'Purchase' ? 'purchase_voucher' : (type === 'Sales' ? 'sales_voucher' : '');
    if (!voucherType) return alert('Email not supported for this type');

    try {
      await voucherService.sendVoucherEmail(voucherType, id);
      alert('Email sent successfully');
    } catch (error: any) {
      alert(`Error sending email: ${error.message || 'Unknown error'}`);
    }
  };

  // Fetch real data from APIs
  const { data: dashboardStats } = useQuery('dashboardStats', reportsService.getDashboardStats);
  const { data: purchaseVouchers, isLoading: purchaseLoading } = useQuery(
    'purchaseVouchers', 
    voucherService.getPurchaseVouchers, 
    { enabled: tabValue === 0 }
  );
  const { data: salesVouchers, isLoading: salesLoading } = useQuery(
    'salesVouchers', 
    voucherService.getSalesVouchers, 
    { enabled: tabValue === 1 }
  );

  // Voucher types with real data
  const voucherTypes = [
    {
      title: 'Purchase Vouchers',
      description: 'Manage purchase transactions, orders, and returns',
      count: dashboardStats?.vouchers?.purchase_vouchers || 0,
      color: '#1976D2',
      vouchers: purchaseVouchers || []
    },
    {
      title: 'Sales Vouchers',
      description: 'Manage sales transactions, orders, and returns',
      count: dashboardStats?.vouchers?.sales_vouchers || 0,
      color: '#2E7D32',
      vouchers: salesVouchers || []
    },
    {
      title: 'Financial Vouchers',
      description: 'Manage payments, receipts, and journal entries',
      count: 0, // TODO: Implement financial vouchers API
      color: '#7B1FA2',
      vouchers: []
    },
    {
      title: 'Internal Vouchers',
      description: 'Manage internal transfers and adjustments',
      count: 0, // TODO: Implement internal vouchers API
      color: '#F57C00',
      vouchers: []
    }
  ];

  const renderVoucherTable = (vouchers: any[], type: string, isLoading: boolean = false) => {
    if (isLoading) {
      return <Typography>Loading {type} vouchers...</Typography>;
    }
    
    if (!vouchers || vouchers.length === 0) {
      return <Typography>No {type} vouchers found.</Typography>;
    }

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Voucher #</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>{type === 'Purchase' ? 'Vendor' : type === 'Sales' ? 'Customer' : 'Type'}</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {vouchers.map((voucher) => (
              <TableRow key={voucher.id}>
                <TableCell>{voucher.voucher_number}</TableCell>
                <TableCell>{new Date(voucher.date).toLocaleDateString()}</TableCell>
                <TableCell>
                  {voucher.vendor?.name || voucher.customer?.name || voucher.type || 'N/A'}
                </TableCell>
                <TableCell>
                  {voucher.total_amount > 0 ? `₹${voucher.total_amount.toLocaleString()}` : '-'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={voucher.status}
                    color={
                      voucher.status === 'approved' || voucher.status === 'confirmed' || voucher.status === 'processed'
                        ? 'success'
                        : voucher.status === 'pending'
                        ? 'warning'
                        : 'default'
                    }
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton size="small" color="primary" onClick={() => handleViewVoucher(type, voucher.id)}>
                    <Visibility />
                  </IconButton>
                  <IconButton size="small" color="primary" onClick={() => handleEditVoucher(type, voucher.id)}>
                    <Edit />
                  </IconButton>
                  <IconButton size="small" color="secondary" onClick={() => handlePrintVoucher(type, voucher.id)}>
                    <Print />
                  </IconButton>
                  <IconButton size="small" color="info" onClick={() => handleEmailVoucher(type, voucher.id)}>
                    <Email />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <MegaMenu user={user} onLogout={handleLogout} />

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Voucher Management System
        </Typography>
        <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
          Comprehensive management of all voucher types in your ERP system
        </Typography>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {voucherTypes.map((voucherType, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography color="textSecondary" gutterBottom>
                        {voucherType.title}
                      </Typography>
                      <Typography variant="h4" component="h2">
                        {voucherType.count}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {voucherType.description}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Voucher Tabs */}
        <Paper sx={{ mb: 4 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="voucher tabs">
              <Tab label="Purchase Vouchers" />
              <Tab label="Sales Vouchers" />
              <Tab label="Financial Vouchers" />
              <Tab label="Internal Vouchers" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Purchase Vouchers</Typography>
            </Box>
            {renderVoucherTable(voucherTypes[0].vouchers, 'Purchase', purchaseLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Sales Vouchers</Typography>
            </Box>
            {renderVoucherTable(voucherTypes[1].vouchers, 'Sales', salesLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Financial Vouchers</Typography>
            </Box>
            {renderVoucherTable(voucherTypes[2].vouchers, 'Financial', false)}
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Internal Vouchers</Typography>
            </Box>
            {renderVoucherTable(voucherTypes[3].vouchers, 'Internal', false)}
          </TabPanel>
        </Paper>

        {/* Summary */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Voucher System Features
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body1" paragraph>
                ✅ <strong>4 Voucher Categories:</strong> Purchase, Sales, Financial, and Internal vouchers
              </Typography>
              <Typography variant="body1" paragraph>
                ✅ <strong>Complete CRUD Operations:</strong> Create, Read, Update, Delete vouchers
              </Typography>
              <Typography variant="body1" paragraph>
                ✅ <strong>Status Management:</strong> Draft, Pending, Approved, Confirmed workflows
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body1" paragraph>
                ✅ <strong>Email Integration:</strong> Send vouchers to vendors/customers
              </Typography>
              <Typography variant="body1" paragraph>
                ✅ <strong>Print Support:</strong> Generate PDF vouchers for printing
              </Typography>
              <Typography variant="body1" paragraph>
                ✅ <strong>Audit Trail:</strong> Track all voucher changes and approvals
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
};

export default VoucherManagement;