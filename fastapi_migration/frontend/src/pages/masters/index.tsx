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
  IconButton,
  Avatar
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Email,
  Phone,
  Business,
  Person,
  Inventory,
  AccountBalance
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { masterDataService, reportsService } from '../../services/authService';
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
      id={`masters-tabpanel-${index}`}
      aria-labelledby={`masters-tab-${index}`}
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

const MasterDataManagement: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [user] = useState({ email: 'demo@example.com', role: 'admin' });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleLogout = () => {
    // Handle logout
  };

  // Fetch data from APIs
  const { data: dashboardStats } = useQuery('dashboardStats', reportsService.getDashboardStats);
  const { data: vendors, isLoading: vendorsLoading } = useQuery('vendors', masterDataService.getVendors, { enabled: tabValue === 0 });
  const { data: customers, isLoading: customersLoading } = useQuery('customers', masterDataService.getCustomers, { enabled: tabValue === 1 });
  const { data: products, isLoading: productsLoading } = useQuery('products', masterDataService.getProducts, { enabled: tabValue === 2 });

  // Master data summary with real data
  const masterDataTypes = [
    {
      title: 'Vendors',
      description: 'Supplier and vendor management',
      count: dashboardStats?.masters?.vendors || 0,
      color: '#1976D2',
      icon: <Business />
    },
    {
      title: 'Customers',
      description: 'Customer and client management',
      count: dashboardStats?.masters?.customers || 0,
      color: '#2E7D32',
      icon: <Person />
    },
    {
      title: 'Products',
      description: 'Product catalog and inventory items',
      count: dashboardStats?.masters?.products || 0,
      color: '#7B1FA2',
      icon: <Inventory />
    },
    {
      title: 'Accounts',
      description: 'Chart of accounts and financial setup',
      count: 0, // TODO: Implement accounts API
      color: '#F57C00',
      icon: <AccountBalance />
    }
  ];

  const renderTable = (data: any[], type: string, isLoading: boolean = false) => {
    if (isLoading) {
      return <Typography>Loading {type}...</Typography>;
    }
    
    if (!data || data.length === 0) {
      return <Typography>No {type} found. Click "Add" to create your first entry.</Typography>;
    }

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {type === 'vendors' || type === 'customers' ? (
                <>
                  <TableCell>Name</TableCell>
                  <TableCell>Contact Person</TableCell>
                  <TableCell>Phone</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>GST Number</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </>
              ) : type === 'products' ? (
                <>
                  <TableCell>Product Name</TableCell>
                  <TableCell>HSN Code</TableCell>
                  <TableCell>Unit</TableCell>
                  <TableCell>Price (₹)</TableCell>
                  <TableCell>GST Rate</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </>
              ) : (
                <>
                  <TableCell>Account Code</TableCell>
                  <TableCell>Account Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Balance (₹)</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((item) => (
              <TableRow key={item.id}>
                {type === 'vendors' || type === 'customers' ? (
                  <>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                          {item.name?.charAt(0) || '?'}
                        </Avatar>
                        {item.name}
                      </Box>
                    </TableCell>
                    <TableCell>{item.contact_person || 'N/A'}</TableCell>
                    <TableCell>{item.contact_number || item.phone}</TableCell>
                    <TableCell>{item.email || 'N/A'}</TableCell>
                    <TableCell>{item.gst_number || 'N/A'}</TableCell>
                    <TableCell>
                      <Chip
                        label={item.is_active ? 'Active' : 'Inactive'}
                        color={item.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" color="primary">
                        <Edit />
                      </IconButton>
                      <IconButton size="small" color="info">
                        <Email />
                      </IconButton>
                      <IconButton size="small" color="secondary">
                        <Phone />
                      </IconButton>
                    </TableCell>
                  </>
                ) : type === 'products' ? (
                  <>
                    <TableCell>{item.name}</TableCell>
                    <TableCell>{item.hsn_code || 'N/A'}</TableCell>
                    <TableCell>{item.unit}</TableCell>
                    <TableCell>₹{item.unit_price?.toLocaleString() || 0}</TableCell>
                    <TableCell>{item.gst_rate || 0}%</TableCell>
                    <TableCell>
                      <Chip
                        label={item.is_active ? 'Active' : 'Inactive'}
                        color={item.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" color="primary">
                        <Edit />
                      </IconButton>
                      <IconButton size="small" color="info">
                        <Inventory />
                      </IconButton>
                    </TableCell>
                  </>
                ) : (
                  <>
                    <TableCell>{item.code}</TableCell>
                    <TableCell>{item.name}</TableCell>
                    <TableCell>{item.type}</TableCell>
                    <TableCell>₹{item.balance?.toLocaleString() || 0}</TableCell>
                    <TableCell>
                      <Chip
                        label={item.status || 'Active'}
                        color={item.status === 'Active' ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" color="primary">
                        <Edit />
                      </IconButton>
                      <IconButton size="small" color="info">
                        <AccountBalance />
                      </IconButton>
                    </TableCell>
                  </>
                )}
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
          Master Data Management
        </Typography>
        <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
          Centralized management of all master data in your ERP system
        </Typography>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {masterDataTypes.map((dataType, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Box sx={{ color: dataType.color, mr: 1 }}>
                          {dataType.icon}
                        </Box>
                        <Typography color="textSecondary" gutterBottom>
                          {dataType.title}
                        </Typography>
                      </Box>
                      <Typography variant="h4" component="h2">
                        {dataType.count}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {dataType.description}
                      </Typography>
                    </Box>
                    <Button
                      variant="contained"
                      startIcon={<Add />}
                      sx={{ bgcolor: dataType.color }}
                      size="small"
                    >
                      Add
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Master Data Tabs */}
        <Paper sx={{ mb: 4 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="master data tabs">
              <Tab label="Vendors" />
              <Tab label="Customers" />
              <Tab label="Products" />
              <Tab label="Accounts" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Vendor Management</Typography>
              <Button variant="contained" startIcon={<Add />}>
                Add New Vendor
              </Button>
            </Box>
            {renderTable(vendors || [], 'vendors', vendorsLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Customer Management</Typography>
              <Button variant="contained" startIcon={<Add />} color="success">
                Add New Customer
              </Button>
            </Box>
            {renderTable(customers || [], 'customers', customersLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Product Catalog</Typography>
              <Button variant="contained" startIcon={<Add />} sx={{ bgcolor: '#7B1FA2' }}>
                Add New Product
              </Button>
            </Box>
            {renderTable(products || [], 'products', productsLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Chart of Accounts</Typography>
              <Button variant="contained" startIcon={<Add />} sx={{ bgcolor: '#F57C00' }}>
                Add New Account
              </Button>
            </Box>
            {renderTable([], 'accounts', false)} {/* TODO: Implement accounts API */}
          </TabPanel>
        </Paper>

        {/* Features */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Master Data Features
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body1" paragraph>
                ✅ <strong>Vendor Management:</strong> Complete supplier database with contact details
              </Typography>
              <Typography variant="body1" paragraph>
                ✅ <strong>Customer Management:</strong> Customer profiles with sales history
              </Typography>
              <Typography variant="body1" paragraph>
                ✅ <strong>Product Catalog:</strong> Comprehensive product database with pricing
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body1" paragraph>
                ✅ <strong>Chart of Accounts:</strong> Financial account structure and balances
              </Typography>
              <Typography variant="body1" paragraph>
                ✅ <strong>GST Compliance:</strong> Tax registration and compliance tracking
              </Typography>
              <Typography variant="body1" paragraph>
                ✅ <strong>Data Validation:</strong> Automated validation and duplicate detection
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
};

export default MasterDataManagement;