// pages/masters.tsx
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
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert
} from '@mui/material';
import { Add, Edit, Delete, Visibility } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import MegaMenu from '../components/MegaMenu';
import ExcelImportExport from '../components/ExcelImportExport';
import { getVendors, getCustomers, getProducts, bulkImportVendors, bulkImportCustomers, bulkImportProducts } from '../services/masterService';

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

const MastersManagement: React.FC = () => {
  const router = useRouter();
  const { tab } = router.query;
  const [tabValue, setTabValue] = useState(0);
  const [user] = useState({ email: 'demo@example.com', role: 'admin' });
  const [editDialog, setEditDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [formData, setFormData] = useState({ name: '', address: '', contact: '' }); // Adjust fields as needed

  const queryClient = useQueryClient();

  useEffect(() => {
    switch (tab) {
      case 'vendors':
        setTabValue(0);
        break;
      case 'customers':
        setTabValue(1);
        break;
      case 'products':
        setTabValue(2);
        break;
      default:
        setTabValue(0);
    }
  }, [tab]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    const tabs = ['vendors', 'customers', 'products'];
    router.push(`/masters?tab=${tabs[newValue]}`, undefined, { shallow: true });
  };

  const handleLogout = () => {
    // Handle logout
  };

  // Fetch data
  const { data: vendors, isLoading: vendorsLoading } = useQuery('vendors', getVendors);
  const { data: customers, isLoading: customersLoading } = useQuery('customers', getCustomers);
  const { data: products, isLoading: productsLoading } = useQuery('products', getProducts);

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

  // Example mutation for editing item (implement similar for create/delete)
  const editItemMutation = useMutation(
    (data: any) => {
      // Assume update endpoint based on entity
      // For example: masterDataService.updateVendor(data.id, data)
      return Promise.resolve(); // Replace with actual service call
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['vendors', 'customers', 'products']);
        setEditDialog(false);
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

  const openEditDialog = (item: any) => {
    setSelectedItem(item);
    setFormData({ name: item.name, address: item.address || '', contact: item.contact || '' }); // Adjust fields
    setEditDialog(true);
  };

  const handleEditSubmit = () => {
    editItemMutation.mutate({ ...selectedItem, ...formData });
  };

  const renderTable = (data: any[], columns: string[], entity: string, isLoading: boolean) => {
    if (isLoading) return <Typography>Loading {entity.toLowerCase()}...</Typography>;
    if (!data || data.length === 0) return <Typography>No {entity.toLowerCase()} available.</Typography>;

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {columns.map(col => <TableCell key={col}>{col}</TableCell>)}
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((item) => (
              <TableRow key={item.id}>
                {columns.map(col => <TableCell key={col}>{item[col.toLowerCase()] || '-'}</TableCell>)}
                <TableCell>
                  <IconButton onClick={() => openEditDialog(item)}><Edit /></IconButton>
                  <IconButton><Visibility /></IconButton>
                  <IconButton><Delete /></IconButton>
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
          Masters Management
        </Typography>

        <Paper sx={{ mb: 4 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Vendors" />
            <Tab label="Customers" />
            <Tab label="Products" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Vendors</Typography>
              <Button variant="contained" startIcon={<Add />}>Add Vendor</Button>
            </Box>
            <ExcelImportExport data={vendors || []} entity="Vendors" onImport={handleImport('Vendors')} />
            {renderTable(vendors || [], ['Name', 'Address', 'Contact'], 'Vendors', vendorsLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Customers</Typography>
              <Button variant="contained" startIcon={<Add />}>Add Customer</Button>
            </Box>
            <ExcelImportExport data={customers || []} entity="Customers" onImport={handleImport('Customers')} />
            {renderTable(customers || [], ['Name', 'Address', 'Contact'], 'Customers', customersLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Products</Typography>
              <Button variant="contained" startIcon={<Add />}>Add Product</Button>
            </Box>
            <ExcelImportExport data={products || []} entity="Products" onImport={handleImport('Products')} />
            {renderTable(products || [], ['Name', 'HSN Code', 'Unit', 'Unit Price'], 'Products', productsLoading)}
          </TabPanel>
        </Paper>
      </Container>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Item</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Address"
            value={formData.address}
            onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Contact"
            value={formData.contact}
            onChange={(e) => setFormData(prev => ({ ...prev, contact: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={handleEditSubmit} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MastersManagement;