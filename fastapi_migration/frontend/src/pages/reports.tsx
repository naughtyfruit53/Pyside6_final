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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Assessment,
  TrendingUp,
  TrendingDown,
  Download,
  Print,
  Refresh,
  Business,
  Person,
  Inventory,
  Warning
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { reportsService } from '../services/authService';
import MegaMenu from '../components/MegaMenu';

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
      id={`reports-tabpanel-${index}`}
      aria-labelledby={`reports-tab-${index}`}
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

const ReportsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [user] = useState({ email: 'demo@example.com', role: 'admin' });
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0], // First day of current month
    end: new Date().toISOString().split('T')[0]
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleLogout = () => {
    // Handle logout
  };

  const handleDateChange = (field: 'start' | 'end', value: string) => {
    setDateRange(prev => ({ ...prev, [field]: value }));
  };

  // Fetch dashboard statistics
  const { data: dashboardStats, isLoading: statsLoading, refetch: refetchStats } = useQuery(
    'dashboardStats',
    reportsService.getDashboardStats,
    {
      enabled: true,
      refetchInterval: 30000 // Refresh every 30 seconds
    }
  );

  // Fetch sales report
  const { data: salesReport, isLoading: salesLoading, refetch: refetchSales } = useQuery(
    ['salesReport', dateRange.start, dateRange.end],
    () => reportsService.getSalesReport({
      start_date: dateRange.start,
      end_date: dateRange.end
    }),
    {
      enabled: tabValue === 1
    }
  );

  // Fetch purchase report
  const { data: purchaseReport, isLoading: purchaseLoading, refetch: refetchPurchase } = useQuery(
    ['purchaseReport', dateRange.start, dateRange.end],
    () => reportsService.getPurchaseReport({
      start_date: dateRange.start,
      end_date: dateRange.end
    }),
    {
      enabled: tabValue === 2
    }
  );

  // Fetch inventory report
  const { data: inventoryReport, isLoading: inventoryLoading, refetch: refetchInventory } = useQuery(
    'inventoryReport',
    () => reportsService.getInventoryReport(false),
    {
      enabled: tabValue === 3
    }
  );

  // Fetch pending orders
  const { data: pendingOrders, isLoading: ordersLoading, refetch: refetchOrders } = useQuery(
    'pendingOrders',
    () => reportsService.getPendingOrders('all'),
    {
      enabled: tabValue === 4
    }
  );

  const renderSummaryCards = () => {
    if (statsLoading || !dashboardStats) {
      return <Typography>Loading statistics...</Typography>;
    }

    const cards = [
      {
        title: 'Vendors',
        value: dashboardStats.masters?.vendors || 0,
        color: '#1976D2',
        icon: <Business />
      },
      {
        title: 'Customers', 
        value: dashboardStats.masters?.customers || 0,
        color: '#2E7D32',
        icon: <Person />
      },
      {
        title: 'Products',
        value: dashboardStats.masters?.products || 0,
        color: '#7B1FA2',
        icon: <Inventory />
      },
      {
        title: 'Low Stock Items',
        value: dashboardStats.inventory?.low_stock_items || 0,
        color: '#F57C00',
        icon: <Warning />
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

  const renderVoucherTable = (vouchers: any[], title: string) => (
    <TableContainer component={Paper}>
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">{title}</Typography>
        <Box>
          <Button startIcon={<Download />} size="small" sx={{ mr: 1 }}>
            Export
          </Button>
          <Button startIcon={<Print />} size="small">
            Print
          </Button>
        </Box>
      </Box>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Voucher #</TableCell>
            <TableCell>Date</TableCell>
            <TableCell>Party</TableCell>
            <TableCell>Amount</TableCell>
            <TableCell>GST</TableCell>
            <TableCell>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {vouchers?.map((voucher) => (
            <TableRow key={voucher.id}>
              <TableCell>{voucher.voucher_number}</TableCell>
              <TableCell>{new Date(voucher.date).toLocaleDateString()}</TableCell>
              <TableCell>{voucher.vendor_name || voucher.customer_name}</TableCell>
              <TableCell>₹{voucher.total_amount.toLocaleString()}</TableCell>
              <TableCell>₹{voucher.gst_amount.toLocaleString()}</TableCell>
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
  );

  return (
    <Box sx={{ flexGrow: 1 }}>
      <MegaMenu user={user} onLogout={handleLogout} />

        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Reports & Analytics
          </Typography>
          <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
            Comprehensive business reports and data analytics
          </Typography>

          {/* Summary Cards */}
          <Box sx={{ mb: 4 }}>
            {renderSummaryCards()}
          </Box>

          {/* Reports Tabs */}
          <Paper sx={{ mb: 4 }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={handleTabChange} aria-label="reports tabs">
                <Tab label="Overview" />
                <Tab label="Sales Report" />
                <Tab label="Purchase Report" />
                <Tab label="Inventory Report" />
                <Tab label="Pending Orders" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <Typography variant="h6" gutterBottom>
                Business Overview
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Sales Performance
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <TrendingUp sx={{ color: 'green', mr: 1 }} />
                        <Typography variant="body1">
                          Total Sales Vouchers: {dashboardStats?.vouchers?.sales_vouchers || 0}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Purchase Performance
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <TrendingDown sx={{ color: 'orange', mr: 1 }} />
                        <Typography variant="body1">
                          Total Purchase Vouchers: {dashboardStats?.vouchers?.purchase_vouchers || 0}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
                <TextField
                  label="Start Date"
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => handleDateChange('start', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  size="small"
                />
                <TextField
                  label="End Date"
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => handleDateChange('end', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  size="small"
                />
                <Button variant="contained" startIcon={<Refresh />} onClick={() => refetchSales()}>
                  Refresh
                </Button>
              </Box>
              
              {salesLoading ? (
                <Typography>Loading sales report...</Typography>
              ) : salesReport ? (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6">Summary</Typography>
                    <Typography>Total Vouchers: {salesReport.summary?.total_vouchers || 0}</Typography>
                    <Typography>Total Sales: ₹{salesReport.summary?.total_sales?.toLocaleString() || 0}</Typography>
                    <Typography>Total GST: ₹{salesReport.summary?.total_gst?.toLocaleString() || 0}</Typography>
                  </Box>
                  {renderVoucherTable(salesReport.vouchers || [], 'Sales Vouchers')}
                </>
              ) : (
                <Typography>No sales data available</Typography>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
                <TextField
                  label="Start Date"
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => handleDateChange('start', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  size="small"
                />
                <TextField
                  label="End Date"
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => handleDateChange('end', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  size="small"
                />
                <Button variant="contained" startIcon={<Refresh />} onClick={() => refetchPurchase()}>
                  Refresh
                </Button>
              </Box>
              
              {purchaseLoading ? (
                <Typography>Loading purchase report...</Typography>
              ) : purchaseReport ? (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6">Summary</Typography>
                    <Typography>Total Vouchers: {purchaseReport.summary?.total_vouchers || 0}</Typography>
                    <Typography>Total Purchases: ₹{purchaseReport.summary?.total_purchases?.toLocaleString() || 0}</Typography>
                    <Typography>Total GST: ₹{purchaseReport.summary?.total_gst?.toLocaleString() || 0}</Typography>
                  </Box>
                  {renderVoucherTable(purchaseReport.vouchers || [], 'Purchase Vouchers')}
                </>
              ) : (
                <Typography>No purchase data available</Typography>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={3}>
              <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h6">Inventory Status</Typography>
                <Button variant="contained" startIcon={<Refresh />} onClick={() => refetchInventory()}>
                  Refresh
                </Button>
              </Box>
              
              {inventoryLoading ? (
                <Typography>Loading inventory report...</Typography>
              ) : inventoryReport ? (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Typography>Total Items: {inventoryReport.summary?.total_items || 0}</Typography>
                    <Typography>Total Value: ₹{inventoryReport.summary?.total_value?.toLocaleString() || 0}</Typography>
                    <Typography>Low Stock Items: {inventoryReport.summary?.low_stock_items || 0}</Typography>
                  </Box>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Product</TableCell>
                          <TableCell>Quantity</TableCell>
                          <TableCell>Unit</TableCell>
                          <TableCell>Unit Price</TableCell>
                          <TableCell>Total Value</TableCell>
                          <TableCell>Status</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {inventoryReport.items?.map((item: any) => (
                          <TableRow key={item.product_id}>
                            <TableCell>{item.product_name}</TableCell>
                            <TableCell>{item.quantity}</TableCell>
                            <TableCell>{item.unit}</TableCell>
                            <TableCell>₹{item.unit_price.toLocaleString()}</TableCell>
                            <TableCell>₹{item.total_value.toLocaleString()}</TableCell>
                            <TableCell>
                              <Chip
                                label={item.is_low_stock ? 'Low Stock' : 'Normal'}
                                color={item.is_low_stock ? 'warning' : 'success'}
                                size="small"
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              ) : (
                <Typography>No inventory data available</Typography>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={4}>
              <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h6">Pending Orders</Typography>
                <Button variant="contained" startIcon={<Refresh />} onClick={() => refetchOrders()}>
                  Refresh
                </Button>
              </Box>
              
              {ordersLoading ? (
                <Typography>Loading pending orders...</Typography>
              ) : pendingOrders ? (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Typography>Total Orders: {pendingOrders.summary?.total_orders || 0}</Typography>
                    <Typography>Total Value: ₹{pendingOrders.summary?.total_value?.toLocaleString() || 0}</Typography>
                  </Box>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Type</TableCell>
                          <TableCell>Order #</TableCell>
                          <TableCell>Date</TableCell>
                          <TableCell>Party</TableCell>
                          <TableCell>Amount</TableCell>
                          <TableCell>Status</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {pendingOrders.orders?.map((order: any) => (
                          <TableRow key={`${order.type}-${order.id}`}>
                            <TableCell>{order.type}</TableCell>
                            <TableCell>{order.number}</TableCell>
                            <TableCell>{new Date(order.date).toLocaleDateString()}</TableCell>
                            <TableCell>{order.party}</TableCell>
                            <TableCell>₹{order.amount.toLocaleString()}</TableCell>
                            <TableCell>
                              <Chip
                                label={order.status}
                                color={order.status === 'pending' ? 'warning' : 'default'}
                                size="small"
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              ) : (
                <Typography>No pending orders</Typography>
              )}
            </TabPanel>
          </Paper>
        </Container>
      </Box>
  );
};

export default ReportsPage;