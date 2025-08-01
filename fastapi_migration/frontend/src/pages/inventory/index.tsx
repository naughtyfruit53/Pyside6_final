// pages/inventory/index.tsx
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
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert
} from '@mui/material';
import {
  Add,
  Edit,
  Refresh,
  Warning,
  TrendingUp,
  TrendingDown,
  Inventory,
  SwapHoriz,
  Visibility
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { masterDataService } from '../../services/authService';
import ExcelImportExport from '../../components/ExcelImportExport';

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
      id={`inventory-tabpanel-${index}`}
      aria-labelledby={`inventory-tab-${index}`}
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

const InventoryManagement: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [user] = useState({ email: 'demo@example.com', role: 'admin' });
  const [adjustmentDialog, setAdjustmentDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [adjustment, setAdjustment] = useState({ quantity: '', reason: '' });

  const queryClient = useQueryClient();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleLogout = () => {
    // Handle logout
  };

  // Fetch data from APIs
  const { data: stock, isLoading: stockLoading, refetch: refetchStock } = useQuery(
    'stock', 
    masterDataService.getStock,
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  const { data: lowStock, isLoading: lowStockLoading } = useQuery(
    'lowStock', 
    masterDataService.getLowStock,
    { enabled: tabValue === 1 }
  );

  // Stock adjustment mutation
  const adjustStockMutation = useMutation(
    ({ productId, quantityChange, reason }: { productId: number, quantityChange: number, reason: string }) =>
      masterDataService.adjustStock(productId, quantityChange, reason),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('stock');
        queryClient.invalidateQueries('lowStock');
        setAdjustmentDialog(false);
        setAdjustment({ quantity: '', reason: '' });
        setSelectedProduct(null);
      }
    }
  );

  const importStockMutation = useMutation(masterDataService.bulkImportStock, {
    onSuccess: () => {
      queryClient.invalidateQueries('stock');
      queryClient.invalidateQueries('lowStock');
    }
  });

  const handleImportStock = (importedData: any[]) => {
    // Convert imported data back to a format the API expects
    // This is a temporary workaround for the type mismatch
    console.log('Imported stock data:', importedData);
    // For now, just refetch stock data instead of sending to API
    refetchStock();
  };

  const handleAdjustStock = () => {
    if (selectedProduct && adjustment.quantity && adjustment.reason) {
      adjustStockMutation.mutate({
        productId: selectedProduct.product_id,
        quantityChange: parseFloat(adjustment.quantity),
        reason: adjustment.reason
      });
    }
  };

  const openAdjustmentDialog = (product: any) => {
    setSelectedProduct(product);
    setAdjustmentDialog(true);
  };

  const renderStockTable = (stockItems: any[], showLowStockOnly = false, isLoading = false) => {
    if (isLoading) {
      return <Typography>Loading stock data...</Typography>;
    }
    
    if (!stockItems || stockItems.length === 0) {
      return <Typography>No stock data available.</Typography>;
    }

    const filteredItems = showLowStockOnly 
      ? stockItems.filter(item => item.is_low_stock || (item.quantity <= (item.reorder_level || 0)))
      : stockItems;

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product Name</TableCell>
              <TableCell>Current Stock</TableCell>
              <TableCell>Unit</TableCell>
              <TableCell>Unit Price</TableCell>
              <TableCell>Total Value</TableCell>
              <TableCell>Reorder Level</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredItems.map((item) => (
              <TableRow key={item.product_id || item.id}>
                <TableCell>{item.product_name}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {item.quantity}
                    {item.quantity <= (item.reorder_level || 0) && (
                      <Warning sx={{ color: 'orange', ml: 1 }} />
                    )}
                  </Box>
                </TableCell>
                <TableCell>{item.unit}</TableCell>
                <TableCell>₹{(item.unit_price || 0).toLocaleString()}</TableCell>
                <TableCell>₹{(item.total_value || (item.quantity * (item.unit_price || 0))).toLocaleString()}</TableCell>
                <TableCell>{item.reorder_level || 0}</TableCell>
                <TableCell>
                  <Chip
                    label={
                      item.quantity <= (item.reorder_level || 0) ? 'Low Stock' : 
                      item.quantity === 0 ? 'Out of Stock' : 'Normal'
                    }
                    color={
                      item.quantity === 0 ? 'error' :
                      item.quantity <= (item.reorder_level || 0) ? 'warning' : 'success'
                    }
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton 
                    size="small" 
                    color="primary"
                    onClick={() => openAdjustmentDialog(item)}
                  >
                    <Edit />
                  </IconButton>
                  <IconButton size="small" color="info">
                    <Visibility />
                  </IconButton>
                  <IconButton size="small" color="secondary">
                    <SwapHoriz />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderSummaryCards = () => {
    if (stockLoading || !stock) {
      return <Typography>Loading inventory summary...</Typography>;
    }

    const totalItems = stock.length;
    const totalValue = stock.reduce((sum: number, item: any) => 
      sum + (item.total_value || (item.quantity * (item.unit_price || 0))), 0
    );
    const lowStockItems = stock.filter((item: any) => 
      item.quantity <= (item.reorder_level || 0)
    ).length;
    const outOfStockItems = stock.filter((item: any) => item.quantity === 0).length;

    const cards = [
      {
        title: 'Total Items',
        value: totalItems,
        color: '#1976D2',
        icon: <Inventory />
      },
      {
        title: 'Total Value',
        value: `₹${totalValue.toLocaleString()}`,
        color: '#2E7D32',
        icon: <TrendingUp />
      },
      {
        title: 'Low Stock Items',
        value: lowStockItems,
        color: '#F57C00',
        icon: <Warning />
      },
      {
        title: 'Out of Stock',
        value: outOfStockItems,
        color: '#D32F2F',
        icon: <TrendingDown />
      }
    ];

    return (
      <Grid container spacing={3}>
        {cards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {card.title}
                    </Typography>
                    <Typography variant="h4" component="h2">
                      {card.value}
                    </Typography>
                  </Box>
                  <Box sx={{ color: card.color }}>
                    {card.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Inventory Management
            </Typography>
            <Typography variant="body1" color="textSecondary">
              Real-time stock monitoring and inventory control
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={() => refetchStock()}
          >
            Refresh Stock
          </Button>
        </Box>

        {/* Summary Cards */}
        <Box sx={{ mb: 4 }}>
          {renderSummaryCards()}
        </Box>

        {/* Inventory Tabs */}
        <Paper sx={{ mb: 4 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="inventory tabs">
              <Tab label="Current Stock" />
              <Tab label="Low Stock Alert" />
              <Tab label="Stock Movements" />
              <Tab label="Stock Valuation" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Current Stock Levels</Typography>
              <Button variant="contained" startIcon={<Add />}>
                Add Stock Entry
              </Button>
            </Box>
            <ExcelImportExport data={stock || []} entity="Stock" onImport={handleImportStock} />
            {renderStockTable(stock || [], false, stockLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ mb: 3 }}>
              <Alert severity="warning" sx={{ mb: 2 }}>
                Items below reorder level require immediate attention
              </Alert>
              <Typography variant="h6">Low Stock Alert</Typography>
            </Box>
            {renderStockTable(lowStock || stock || [], true, lowStockLoading || stockLoading)}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Stock Movements</Typography>
              <Button variant="contained" startIcon={<SwapHoriz />}>
                View All Movements
              </Button>
            </Box>
            <Typography>Stock movement tracking coming soon...</Typography>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Stock Valuation Report</Typography>
              <Button variant="contained" startIcon={<TrendingUp />}>
                Generate Report
              </Button>
            </Box>
            <Typography>Stock valuation reporting coming soon...</Typography>
          </TabPanel>
        </Paper>
      </Container>

      {/* Stock Adjustment Dialog */}
      <Dialog open={adjustmentDialog} onClose={() => setAdjustmentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Adjust Stock: {selectedProduct?.product_name}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Current Stock: {selectedProduct?.quantity} {selectedProduct?.unit}
          </Typography>
          <TextField
            fullWidth
            label="Quantity Change"
            placeholder="Enter positive or negative number"
            value={adjustment.quantity}
            onChange={(e) => setAdjustment(prev => ({ ...prev, quantity: e.target.value }))}
            type="number"
            sx={{ mb: 2 }}
            helperText="Use negative numbers to decrease stock, positive to increase"
          />
          <TextField
            fullWidth
            label="Reason"
            placeholder="Reason for adjustment"
            value={adjustment.reason}
            onChange={(e) => setAdjustment(prev => ({ ...prev, reason: e.target.value }))}
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdjustmentDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleAdjustStock} 
            variant="contained"
            disabled={!adjustment.quantity || !adjustment.reason || adjustStockMutation.isLoading}
          >
            {adjustStockMutation.isLoading ? 'Adjusting...' : 'Adjust Stock'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InventoryManagement;