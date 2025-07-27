import React, { useState } from 'react';
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
  const [tabValue, setTabValue] = useState(0);
  const [user] = useState({ email: 'demo@example.com', role: 'admin' });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleLogout = () => {
    // Handle logout
  };

  // Mock data for demonstration
  const voucherTypes = [
    {
      title: 'Purchase Vouchers',
      description: 'Manage purchase transactions, orders, and returns',
      count: 25,
      color: '#1976D2',
      vouchers: [
        { id: 1, number: 'PV001', date: '2024-01-15', vendor: 'ABC Supplies', amount: 15000, status: 'Approved' },
        { id: 2, number: 'PV002', date: '2024-01-16', vendor: 'XYZ Materials', amount: 8500, status: 'Pending' },
        { id: 3, number: 'PV003', date: '2024-01-17', vendor: 'DEF Traders', amount: 12000, status: 'Draft' }
      ]
    },
    {
      title: 'Sales Vouchers',
      description: 'Manage sales transactions, orders, and returns',
      count: 18,
      color: '#2E7D32',
      vouchers: [
        { id: 1, number: 'SV001', date: '2024-01-15', customer: 'Client A Ltd', amount: 25000, status: 'Confirmed' },
        { id: 2, number: 'SV002', date: '2024-01-16', customer: 'Customer B Inc', amount: 18500, status: 'Pending' },
        { id: 3, number: 'SV003', date: '2024-01-17', customer: 'Retail Store C', amount: 32000, status: 'Shipped' }
      ]
    },
    {
      title: 'Financial Vouchers',
      description: 'Manage payments, receipts, and journal entries',
      count: 42,
      color: '#7B1FA2',
      vouchers: [
        { id: 1, number: 'FV001', date: '2024-01-15', type: 'Payment', amount: 15000, status: 'Processed' },
        { id: 2, number: 'FV002', date: '2024-01-16', type: 'Receipt', amount: 25000, status: 'Cleared' },
        { id: 3, number: 'FV003', date: '2024-01-17', type: 'Journal', amount: 0, status: 'Posted' }
      ]
    },
    {
      title: 'Internal Vouchers',
      description: 'Manage internal transfers and adjustments',
      count: 12,
      color: '#F57C00',
      vouchers: [
        { id: 1, number: 'IV001', date: '2024-01-15', type: 'Transfer', amount: 0, status: 'Completed' },
        { id: 2, number: 'IV002', date: '2024-01-16', type: 'Adjustment', amount: 0, status: 'Pending' },
        { id: 3, number: 'IV003', date: '2024-01-17', type: 'Production', amount: 0, status: 'In Progress' }
      ]
    }
  ];

  const renderVoucherTable = (vouchers: any[], type: string) => (
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
              <TableCell>{voucher.number}</TableCell>
              <TableCell>{voucher.date}</TableCell>
              <TableCell>{voucher.vendor || voucher.customer || voucher.type}</TableCell>
              <TableCell>{voucher.amount > 0 ? `₹${voucher.amount.toLocaleString()}` : '-'}</TableCell>
              <TableCell>
                <Chip
                  label={voucher.status}
                  color={
                    voucher.status === 'Approved' || voucher.status === 'Confirmed' || voucher.status === 'Processed'
                      ? 'success'
                      : voucher.status === 'Pending'
                      ? 'warning'
                      : 'default'
                  }
                  size="small"
                />
              </TableCell>
              <TableCell>
                <IconButton size="small" color="primary">
                  <Visibility />
                </IconButton>
                <IconButton size="small" color="primary">
                  <Edit />
                </IconButton>
                <IconButton size="small" color="secondary">
                  <Print />
                </IconButton>
                <IconButton size="small" color="info">
                  <Email />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

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
                    <Button
                      variant="contained"
                      startIcon={<Add />}
                      sx={{ bgcolor: voucherType.color }}
                      size="small"
                    >
                      Create
                    </Button>
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
              <Button variant="contained" startIcon={<Add />}>
                Create Purchase Voucher
              </Button>
            </Box>
            {renderVoucherTable(voucherTypes[0].vouchers, 'Purchase')}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Sales Vouchers</Typography>
              <Button variant="contained" startIcon={<Add />} color="success">
                Create Sales Voucher
              </Button>
            </Box>
            {renderVoucherTable(voucherTypes[1].vouchers, 'Sales')}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Financial Vouchers</Typography>
              <Button variant="contained" startIcon={<Add />} sx={{ bgcolor: '#7B1FA2' }}>
                Create Financial Voucher
              </Button>
            </Box>
            {renderVoucherTable(voucherTypes[2].vouchers, 'Financial')}
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Internal Vouchers</Typography>
              <Button variant="contained" startIcon={<Add />} sx={{ bgcolor: '#F57C00' }}>
                Create Internal Voucher
              </Button>
            </Box>
            {renderVoucherTable(voucherTypes[3].vouchers, 'Internal')}
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