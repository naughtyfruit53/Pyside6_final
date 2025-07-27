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

  // Mock data for demonstration
  const masterDataTypes = [
    {
      title: 'Vendors',
      description: 'Supplier and vendor management',
      count: 45,
      color: '#1976D2',
      icon: <Business />
    },
    {
      title: 'Customers',
      description: 'Customer and client management',
      count: 128,
      color: '#2E7D32',
      icon: <Person />
    },
    {
      title: 'Products',
      description: 'Product catalog and inventory items',
      count: 234,
      color: '#7B1FA2',
      icon: <Inventory />
    },
    {
      title: 'Accounts',
      description: 'Chart of accounts and financial setup',
      count: 67,
      color: '#F57C00',
      icon: <AccountBalance />
    }
  ];

  const vendors = [
    { id: 1, name: 'ABC Supplies Ltd', contact: 'John Smith', phone: '+91-9876543210', email: 'john@abcsupplies.com', gst: '27ABCDE1234F1Z5', status: 'Active' },
    { id: 2, name: 'XYZ Materials Inc', contact: 'Sarah Johnson', phone: '+91-9876543211', email: 'sarah@xyzmaterials.com', gst: '27XYZAB1234F1Z5', status: 'Active' },
    { id: 3, name: 'DEF Traders', contact: 'Mike Wilson', phone: '+91-9876543212', email: 'mike@deftraders.com', gst: '27DEFGH1234F1Z5', status: 'Inactive' }
  ];

  const customers = [
    { id: 1, name: 'Client A Ltd', contact: 'Emma Davis', phone: '+91-9876543220', email: 'emma@clienta.com', gst: '27CLIENT1234F1Z5', status: 'Active' },
    { id: 2, name: 'Customer B Inc', contact: 'Robert Brown', phone: '+91-9876543221', email: 'robert@customerb.com', gst: '27CUSTB1234F1Z5', status: 'Active' },
    { id: 3, name: 'Retail Store C', contact: 'Lisa Garcia', phone: '+91-9876543222', email: 'lisa@retailc.com', gst: '27RETAIL1234F1Z5', status: 'Active' }
  ];

  const products = [
    { id: 1, name: 'Raw Material A', category: 'Materials', unit: 'KG', price: 150, stock: 500, status: 'Active' },
    { id: 2, name: 'Component B', category: 'Components', unit: 'PCS', price: 25, stock: 1200, status: 'Active' },
    { id: 3, name: 'Finished Product C', category: 'Finished Goods', unit: 'PCS', price: 500, stock: 75, status: 'Low Stock' }
  ];

  const accounts = [
    { id: 1, code: '1001', name: 'Cash in Hand', type: 'Asset', balance: 25000, status: 'Active' },
    { id: 2, code: '2001', name: 'Accounts Payable', type: 'Liability', balance: 45000, status: 'Active' },
    { id: 3, code: '3001', name: 'Sales Revenue', type: 'Income', balance: 125000, status: 'Active' }
  ];

  const renderTable = (data: any[], type: string) => (
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
                <TableCell>Category</TableCell>
                <TableCell>Unit</TableCell>
                <TableCell>Price (₹)</TableCell>
                <TableCell>Stock</TableCell>
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
                        {item.name.charAt(0)}
                      </Avatar>
                      {item.name}
                    </Box>
                  </TableCell>
                  <TableCell>{item.contact}</TableCell>
                  <TableCell>{item.phone}</TableCell>
                  <TableCell>{item.email}</TableCell>
                  <TableCell>{item.gst}</TableCell>
                  <TableCell>
                    <Chip
                      label={item.status}
                      color={item.status === 'Active' ? 'success' : 'default'}
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
                  <TableCell>{item.category}</TableCell>
                  <TableCell>{item.unit}</TableCell>
                  <TableCell>₹{item.price.toLocaleString()}</TableCell>
                  <TableCell>{item.stock}</TableCell>
                  <TableCell>
                    <Chip
                      label={item.status}
                      color={item.status === 'Active' ? 'success' : item.status === 'Low Stock' ? 'warning' : 'default'}
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
                  <TableCell>₹{item.balance.toLocaleString()}</TableCell>
                  <TableCell>
                    <Chip
                      label={item.status}
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
            {renderTable(vendors, 'vendors')}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Customer Management</Typography>
              <Button variant="contained" startIcon={<Add />} color="success">
                Add New Customer
              </Button>
            </Box>
            {renderTable(customers, 'customers')}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Product Catalog</Typography>
              <Button variant="contained" startIcon={<Add />} sx={{ bgcolor: '#7B1FA2' }}>
                Add New Product
              </Button>
            </Box>
            {renderTable(products, 'products')}
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Chart of Accounts</Typography>
              <Button variant="contained" startIcon={<Add />} sx={{ bgcolor: '#F57C00' }}>
                Add New Account
              </Button>
            </Box>
            {renderTable(accounts, 'accounts')}
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