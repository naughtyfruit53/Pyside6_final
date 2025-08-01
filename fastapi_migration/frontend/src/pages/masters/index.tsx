// Revised masters.index.tsx

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
  IconButton,
  Avatar,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  InputLabel,
  FormControl
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
  AccountBalance,
  Visibility
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { masterDataService, reportsService, companyService } from '../../services/authService';
import ExcelImportExport from '../../components/ExcelImportExport';
import { bulkImportVendors, bulkImportCustomers, bulkImportProducts } from '../../services/masterService';

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

const STATE_CODES: { [key: string]: string } = {
  'Jammu & Kashmir': '01',
  'Himachal Pradesh': '02',
  'Punjab': '03',
  'Chandigarh': '04',
  'Uttarakhand': '05',
  'Haryana': '06',
  'Delhi': '07',
  'Rajasthan': '08',
  'Uttar Pradesh': '09',
  'Bihar': '10',
  'Sikkim': '11',
  'Arunachal Pradesh': '12',
  'Nagaland': '13',
  'Manipur': '14',
  'Mizoram': '15',
  'Tripura': '16',
  'Meghalaya': '17',
  'Assam': '18',
  'West Bengal': '19',
  'Jharkhand': '20',
  'Odisha': '21',
  'Chhattisgarh': '22',
  'Madhya Pradesh': '23',
  'Gujarat': '24',
  'Daman & Diu': '25',
  'Dadra & Nagar Haveli': '26',
  'Maharashtra': '27',
  'Andhra Pradesh (Old)': '28',
  'Karnataka': '29',
  'Goa': '30',
  'Lakshadweep': '31',
  'Kerala': '32',
  'Tamil Nadu': '33',
  'Puducherry': '34',
  'Andaman & Nicobar Islands': '35',
  'Telangana': '36',
  'Andhra Pradesh (Newly Added)': '37',
  'Ladakh (Newly Added)': '38',
  'Others Territory': '97',
  'Center Jurisdiction': '99'
};

const MasterDataManagement: React.FC = () => {
  const router = useRouter();
  const { tab, action } = router.query;
  const [tabValue, setTabValue] = useState(0);
  const [user] = useState({ email: 'demo@example.com', role: 'admin' });
  const [itemDialog, setItemDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [formData, setFormData] = useState({
    name: '', 
    address1: '', 
    address2: '', 
    city: '', 
    state: '', 
    state_code: '', 
    pin_code: '', 
    contact: '', 
    email: '', 
    gst_number: '', 
    pan_number: '', 
    part_number: '', 
    hsn_code: '', 
    unit: '', 
    unit_price: 0, 
    gst_rate: 0, 
    is_gst_inclusive: false, 
    reorder_level: 0, 
    description: '', 
    is_manufactured: false, 
    drawings_path: ''
  });

  // Company dialog state
  const [companyEditDialog, setCompanyEditDialog] = useState(false);

  const queryClient = useQueryClient();

  // Update tab from URL and handle auto-open add dialog
  useEffect(() => {
    switch (tab) {
      case 'vendors': setTabValue(0); break;
      case 'customers': setTabValue(1); break;
      case 'products': setTabValue(2); break;
      case 'accounts': setTabValue(3); break;
      case 'company': setTabValue(4); break;
      default: setTabValue(0);
    }
    
    // Auto-open add dialog if action=add in URL
    if (action === 'add') {
      openItemDialog(null);
    }
  }, [tab, action]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    const tabNames = ['vendors', 'customers', 'products', 'accounts', 'company'];
    router.replace(`/masters?tab=${tabNames[newValue]}`, undefined, { shallow: true });
  };

  const handleLogout = () => {
    // Handle logout
  };

  // Fetch data from APIs
  const { data: dashboardStats } = useQuery('dashboardStats', reportsService.getDashboardStats);
  const { data: vendors, isLoading: vendorsLoading } = useQuery('vendors', masterDataService.getVendors, { enabled: tabValue === 0 });
  const { data: customers, isLoading: customersLoading } = useQuery('customers', masterDataService.getCustomers, { enabled: tabValue === 1 });
  const { data: products, isLoading: productsLoading } = useQuery('products', masterDataService.getProducts, { enabled: tabValue === 2 });
  const { data: company } = useQuery('company', companyService.getCurrentCompany, { enabled: tabValue === 4 });

  // Mutations for bulk import
  const importVendorsMutation = useMutation(bulkImportVendors, {
    onSuccess: () => queryClient.invalidateQueries('vendors')
  });
  const importCustomersMutation = useMutation(bulkImportCustomers, {
    onSuccess: () => queryClient.invalidateQueries('customers')
  });
  const importProductsMutation = useMutation(bulkImportProducts, {
    onSuccess: () => queryClient.invalidateQueries('products')
  });

  // Mutation for updating item
  const updateItemMutation = useMutation(
    (data: any) => {
      // Replace with actual service call based on entity
      if (tab === 'vendors') return masterDataService.updateVendor(data.id, data);
      if (tab === 'customers') return masterDataService.updateCustomer(data.id, data);
      if (tab === 'products') return masterDataService.updateProduct(data.id, data);
      return Promise.resolve();
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['vendors', 'customers', 'products']);
        setItemDialog(false);
        setSelectedItem(null);
        resetForm();
        setErrorMessage('');
      },
      onError: (error: any) => {
        console.error('Update error:', error);
        setErrorMessage(error.message || 'Failed to update item. Please check your input.');
      }
    }
  );

  // Mutation for creating item
  const createItemMutation = useMutation(
    (data: any) => {
      // Replace with actual service call based on entity
      if (tab === 'vendors') return masterDataService.createVendor(data);
      if (tab === 'customers') return masterDataService.createCustomer(data);
      if (tab === 'products') return masterDataService.createProduct(data);
      return Promise.resolve();
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['vendors', 'customers', 'products']);
        setItemDialog(false);
        setSelectedItem(null);
        resetForm();
        setErrorMessage('');
        
        // Trigger refresh in parent window if opened from voucher
        if (window.opener) {
          window.opener.localStorage.setItem('refreshMasterData', 'true');
          window.close();
        }
      },
      onError: (error: any) => {
        console.error('Create error:', error);
        setErrorMessage(error.message || 'Failed to create item. Please check your input.');
      }
    }
  );

  const handleImport = (entity: string) => (importedData: any[]) => {
    switch (entity) {
      case 'Vendors':
        importVendorsMutation.mutate(importedData);
        break;
      case 'Customers':
        importCustomersMutation.mutate(importedData);
        break;
      case 'Products':
        importProductsMutation.mutate(importedData);
        break;
    }
  };

  // Company edit dialog functions
  const openCompanyEditDialog = () => {
    setCompanyEditDialog(true);
  };

  const closeCompanyEditDialog = () => {
    setCompanyEditDialog(false);
  };

  const openItemDialog = (item: any = null, targetTab?: number) => {
    if (targetTab !== undefined && targetTab !== tabValue) {
      handleTabChange({} as React.SyntheticEvent, targetTab);
    }
    setSelectedItem(item);
    if (item) {
      setFormData({
        name: item.product_name || '',  // Use product_name consistently
        address1: item.address1 || item.address || '',
        address2: item.address2 || '',
        city: item.city || '',
        state: item.state || '',
        state_code: item.state_code || '',
        pin_code: item.pin_code || '',
        contact: item.contact_number || item.phone || '',
        email: item.email || '',
        gst_number: item.gst_number || '',
        pan_number: item.pan_number || '',
        part_number: item.part_number || '',
        hsn_code: item.hsn_code || '',
        unit: item.unit || '',
        unit_price: item.unit_price || 0,
        gst_rate: item.gst_rate || 0,
        is_gst_inclusive: item.is_gst_inclusive || false,
        reorder_level: item.reorder_level || 0,
        description: item.description || '',
        is_manufactured: item.is_manufactured || false,
        drawings_path: item.drawings_path || ''
      });
    } else {
      resetForm();
    }
    setErrorMessage(''); // Clear any previous error messages
    setItemDialog(true);
  };

  const resetForm = () => {
    setFormData({
      name: '', 
      address1: '', 
      address2: '', 
      city: '', 
      state: '', 
      state_code: '', 
      pin_code: '', 
      contact: '', 
      email: '', 
      gst_number: '', 
      pan_number: '', 
      part_number: '', 
      hsn_code: '', 
      unit: '', 
      unit_price: 0, 
      gst_rate: 0, 
      is_gst_inclusive: false, 
      reorder_level: 0, 
      description: '', 
      is_manufactured: false, 
      drawings_path: ''
    });
  };

  const handleAddClick = () => {
    openItemDialog(null);
  };

  const handleSubmit = () => {
    const data = { ...formData };
    
    // Map frontend field names to backend schema
    if (tabValue === 0 || tabValue === 1) { // Vendors or Customers
      data.contact_number = data.contact; // Map contact to contact_number
      delete data.contact; // Remove old field name
    }
    
    if (selectedItem) {
      updateItemMutation.mutate({ ...selectedItem, ...data });
    } else {
      createItemMutation.mutate(data);
    }
  };

  const handleStateChange = (e: any) => {
    const state = e.target.value;
    const state_code = STATE_CODES[state] || '';
    setFormData(prev => ({ ...prev, state, state_code }));
  };

  const handlePincodeChange = async (e: any) => {
    const pinCode = e.target.value;
    setFormData(prev => ({ ...prev, pin_code: pinCode }));
    
    // Auto-fill city/state/state_code if pinCode is 6 digits
    if (pinCode.length === 6 && /^\d{6}$/.test(pinCode)) {
      try {
        const response = await fetch(`/api/v1/pincode/lookup/${pinCode}`);
        if (response.ok) {
          const data = await response.json();
          setFormData(prev => ({ 
            ...prev, 
            city: data.city,
            state: data.state,
            state_code: data.state_code
          }));
        }
      } catch (error) {
        console.log('Pincode lookup failed:', error);
        // Fail silently, user can enter manually
      }
    }
  };

  // Master data summary with real data
  const masterDataTypes = [
    {
      title: 'Vendors',
      description: 'Supplier and vendor management',
      count: dashboardStats?.masters?.vendors || 0,
      color: '#1976D2',
      icon: <Business />,
      tabIndex: 0
    },
    {
      title: 'Customers',
      description: 'Customer and client management',
      count: dashboardStats?.masters?.customers || 0,
      color: '#2E7D32',
      icon: <Person />,
      tabIndex: 1
    },
    {
      title: 'Products',
      description: 'Product catalog and inventory items',
      count: dashboardStats?.masters?.products || 0,
      color: '#7B1FA2',
      icon: <Inventory />,
      tabIndex: 2
    },
    {
      title: 'Accounts',
      description: 'Chart of accounts and financial setup',
      count: 0, // TODO: Implement accounts API
      color: '#F57C00',
      icon: <AccountBalance />,
      tabIndex: 3
    },
    {
      title: 'Company Details',
      description: 'Your company information and settings',
      count: company ? 1 : 0,
      color: '#1976D2',
      icon: <Business />,
      tabIndex: 4
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
                    <TableCell>{item.contact_number || item.phone || 'N/A'}</TableCell>
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
                      <IconButton size="small" color="primary" onClick={() => openItemDialog(item)}>
                        <Edit />
                      </IconButton>
                      <IconButton size="small" color="info">
                        <Email />
                      </IconButton>
                      <IconButton size="small" color="secondary">
                        <Phone />
                      </IconButton>
                      <IconButton size="small" color="error">
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </>
                ) : type === 'products' ? (
                  <>
                    <TableCell>{item.product_name}</TableCell>
                    <TableCell>{item.hsn_code || 'N/A'}</TableCell>
                    <TableCell>{item.unit || 'N/A'}</TableCell>
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
                      <IconButton size="small" color="primary" onClick={() => openItemDialog(item)}>
                        <Edit/>
                      </IconButton>
                      <IconButton size="small" color="info">
                        <Visibility />
                      </IconButton>
                      <IconButton size="small" color="error">
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </>
                ) : (
                  <>
                    <TableCell>{item.code || 'N/A'}</TableCell>
                    <TableCell>{item.name || 'N/A'}</TableCell>
                    <TableCell>{item.type || 'N/A'}</TableCell>
                    <TableCell>₹{item.balance?.toLocaleString() || 0}</TableCell>
                    <TableCell>
                      <Chip
                        label={item.status || 'Active'}
                        color={item.status === 'Active' ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" color="primary" onClick={() => openItemDialog(item)}>
                        <Edit />
                      </IconButton>
                      <IconButton size="small" color="info">
                        <Visibility />
                      </IconButton>
                      <IconButton size="small" color="error">
                        <Delete />
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

  const renderCompanyDetails = () => {
    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Company Details
        </Typography>
        {company ? (
          <Paper sx={{ p: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Name</Typography>
                <Typography>{company.name}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Business Type</Typography>
                <Typography>{company.business_type}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Industry</Typography>
                <Typography>{company.industry}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Website</Typography>
                <Typography>{company.website}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Primary Email</Typography>
                <Typography>{company.primary_email}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Primary Phone</Typography>
                <Typography>{company.primary_phone}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2">Address</Typography>
                <Typography>
                  {company.address1}, {company.address2}, {company.city}, {company.state} {company.pin_code}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">GST Number</Typography>
                <Typography>{company.gst_number}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">PAN Number</Typography>
                <Typography>{company.pan_number}</Typography>
              </Grid>
            </Grid>
            <Button
              variant="contained"
              startIcon={<Edit />}
              sx={{ mt: 3 }}
              onClick={() => openCompanyEditDialog()}
            >
              Edit Company Details
            </Button>
          </Paper>
        ) : (
          <Alert severity="info">
            No company details found. Please set up your company information.
          </Alert>
        )}
      </Box>
    );
  };

  return (
    <Box sx={{ flexGrow: 1 }}>

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
                      onClick={() => openItemDialog(null, dataType.tabIndex)}
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
              <Tab label="Company" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Vendor Management</Typography>
              <Button variant="contained" startIcon={<Add />} onClick={handleAddClick}>
                Add New Vendor
              </Button>
            </Box>
            <ExcelImportExport data={vendors || []} entity="Vendors" onImport={handleImport('Vendors')} />
            {renderTable(vendors || [], 'vendors', vendorsLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Customer Management</Typography>
              <Button variant="contained" startIcon={<Add />} color="success" onClick={handleAddClick}>
                Add New Customer
              </Button>
            </Box>
            <ExcelImportExport data={customers || []} entity="Customers" onImport={handleImport('Customers')} />
            {renderTable(customers || [], 'customers', customersLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Product Catalog</Typography>
              <Button variant="contained" startIcon={<Add />} sx={{ bgcolor: '#7B1FA2' }} onClick={handleAddClick}>
                Add New Product
              </Button>
            </Box>
            <ExcelImportExport data={products || []} entity="Products" onImport={handleImport('Products')} />
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

          <TabPanel value={tabValue} index={4}>
            {renderCompanyDetails()}
          </TabPanel>
        </Paper>

      </Container>

      {/* Add/Edit Dialog */}
      <Dialog open={itemDialog} onClose={() => setItemDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedItem ? 'Edit' : 'Add'} {tabValue === 0 ? 'Vendor' : tabValue === 1 ? 'Customer' : tabValue === 2 ? 'Product' : 'Account'}</DialogTitle>
        <DialogContent>
          {errorMessage && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {errorMessage}
            </Alert>
          )}
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            sx={{ mb: 2 }}
          />
          {(tabValue === 0 || tabValue === 1) && (
            <>
              <TextField
                fullWidth
                label="Address Line 1"
                value={formData.address1}
                onChange={(e) => setFormData(prev => ({ ...prev, address1: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Address Line 2"
                value={formData.address2}
                onChange={(e) => setFormData(prev => ({ ...prev, address2: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="PIN Code"
                value={formData.pin_code}
                onChange={handlePincodeChange}
                sx={{ mb: 2 }}
                helperText="Enter 6-digit PIN code to auto-fill city and state"
              />
              <TextField
                fullWidth
                label="City"
                value={formData.city}
                onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel id="state-label">State</InputLabel>
                <Select
                  labelId="state-label"
                  value={formData.state}
                  label="State"
                  onChange={handleStateChange}
                >
                  {Object.keys(STATE_CODES).map((state) => (
                    <MenuItem key={state} value={state}>
                      {state}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                fullWidth
                label="State Code"
                value={formData.state_code}
                onChange={(e) => setFormData(prev => ({ ...prev, state_code: e.target.value }))}
                sx={{ mb: 2 }}
                helperText="Auto-filled from PIN code or state selection"
              />
              <TextField
                fullWidth
                label="Phone"
                value={formData.contact}
                onChange={(e) => setFormData(prev => ({ ...prev, contact: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="GST Number"
                value={formData.gst_number}
                onChange={(e) => setFormData(prev => ({ ...prev, gst_number: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="PAN Number"
                value={formData.pan_number}
                onChange={(e) => setFormData(prev => ({ ...prev, pan_number: e.target.value }))}
                sx={{ mb: 2 }}
              />
            </>
          )}
          {tabValue === 2 && (
            <>
              <TextField
                fullWidth
                label="Part Number"
                value={formData.part_number}
                onChange={(e) => setFormData(prev => ({ ...prev, part_number: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="HSN Code"
                value={formData.hsn_code}
                onChange={(e) => setFormData(prev => ({ ...prev, hsn_code: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Unit"
                value={formData.unit}
                onChange={(e) => setFormData(prev => ({ ...prev, unit: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Unit Price"
                type="number"
                value={formData.unit_price}
                onChange={(e) => setFormData(prev => ({ ...prev, unit_price: parseFloat(e.target.value) }))}
                sx={{ mb: 2 }}
              />
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel id="gst-rate-label">GST Rate (%)</InputLabel>
                <Select
                  labelId="gst-rate-label"
                  value={`${formData.gst_rate}%`}
                  label="GST Rate (%)"
                  onChange={(e) => setFormData(prev => ({ ...prev, gst_rate: parseFloat((e.target.value as string).replace('%', '')) }))}
                >
                  <MenuItem value="0%">0%</MenuItem>
                  <MenuItem value="5%">5%</MenuItem>
                  <MenuItem value="12%">12%</MenuItem>
                  <MenuItem value="18%">18%</MenuItem>
                  <MenuItem value="28%">28%</MenuItem>
                </Select>
              </FormControl>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_gst_inclusive}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_gst_inclusive: e.target.checked }))}
                  />
                }
                label="GST Inclusive"
              />
              <TextField
                fullWidth
                label="Reorder Level"
                type="number"
                value={formData.reorder_level}
                onChange={(e) => setFormData(prev => ({ ...prev, reorder_level: parseInt(e.target.value) }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_manufactured}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_manufactured: e.target.checked }))}
                  />
                }
                label="Is Manufactured"
              />
              <TextField
                fullWidth
                label="Drawings Path"
                value={formData.drawings_path}
                onChange={(e) => setFormData(prev => ({ ...prev, drawings_path: e.target.value }))}
                sx={{ mb: 2 }}
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setItemDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MasterDataManagement;