import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { Box, Button, TextField, Typography, Grid, IconButton, Alert, CircularProgress, Container, Checkbox, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Select, MenuItem, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { Add, Remove, Edit, Visibility } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { voucherService } from '../../../services/authService';
import SearchableDropdown from '../../../components/SearchableDropdown';

const numberToWordsInteger = (num: number): string => {
  if (num === 0) return '';
  const belowTwenty = [' ', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
  const tens = [' ', ' ', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
  const thousands = ['', 'Thousand', 'Million', 'Billion'];
  let word = '';
  let i = 0;
  while (num > 0) {
    const chunk = num % 1000;
    if (chunk) {
      let chunkWord = '';
      if (chunk >= 100) {
        chunkWord += belowTwenty[Math.floor(chunk / 100)] + ' Hundred ';
      }
      let remain = chunk % 100;
      if (remain >= 20) {
        chunkWord += tens[Math.floor(remain / 10)] + ' ';
        remain %= 10;
      }
      if (remain > 0) {
        chunkWord += belowTwenty[remain] + ' ';
      }
      word = chunkWord + thousands[i] + ' ' + word;
    }
    num = Math.floor(num / 1000);
    i++;
  }
  return word.trim();
};

const numberToWords = (num: number): string => {
  if (num === 0) return 'Zero';
  const integer = Math.floor(num);
  const decimal = Math.round((num - integer) * 100);
  let word = numberToWordsInteger(integer);
  if (decimal > 0) {
    word += ' point ' + numberToWordsInteger(decimal);
  }
  return word;
};

const PurchaseOrderPage: React.FC = () => {
  const router = useRouter();
  const { id, mode: queryMode } = router.query;
  const [mode, setMode] = useState<'create' | 'edit' | 'view'>((queryMode as any) || 'create');
  const [selectedId, setSelectedId] = useState<number | null>(id ? Number(id) : null);
  const [addVendorDialogOpen, setAddVendorDialogOpen] = useState(false);
  const [addProductDialogOpen, setAddProductDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { control, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm({
    defaultValues: {
      voucher_number: 'PO/2526/00000001',
      date: new Date().toISOString().slice(0, 10),
      required_by_date: new Date().toISOString().slice(0, 10),
      vendor: '',
      payment_terms: '',
      total_amount: 0,
      notes: '',
      items: [{ name: '', hsn_code: '', quantity: 0, unit: '', unit_price: 0, gst: 0, amount: 0 }],
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items'
  });

  const itemsWatch = watch('items');
  const totalAmount = watch('total_amount');

  useEffect(() => {
    let total = 0;
    itemsWatch.forEach((item, index) => {
      const subtotal = (item.quantity || 0) * (item.unit_price || 0);
      const gstAmount = subtotal * ((item.gst || 0) / 100);
      const itemAmount = subtotal + gstAmount;
      setValue(`items.${index}.amount`, itemAmount);
      total += itemAmount;
    });
    setValue('total_amount', total);
  }, [itemsWatch, setValue]);

  const { data: voucherList, isLoading: isLoadingList } = useQuery(
    ['purchaseOrders'],
    () => voucherService.getPurchaseOrders() // Assume this method exists
  );

  const { data: vendorList } = useQuery(
    ['vendors'],
    () => voucherService.getVendors() // Assume this method exists to fetch vendors
  );

  const { data: productList } = useQuery(
    ['products'],
    () => voucherService.getProducts() // Assume this method exists to fetch products
  );

  const { data: voucherData, isLoading: isFetching } = useQuery(
    ['purchaseOrder', selectedId],
    () => voucherService.getPurchaseOrderById(selectedId!),
    { enabled: !!selectedId }
  );

  useEffect(() => {
    if (voucherData) {
      reset(voucherData);
    } else if (mode === 'create') {
      reset({
        voucher_number: 'PO/2526/00000001',
        date: new Date().toISOString().slice(0, 10),
        required_by_date: new Date().toISOString().slice(0, 10),
        vendor: '',
        payment_terms: '',
        total_amount: 0,
        notes: '',
        items: [{ name: '', hsn_code: '', quantity: 0, unit: '', unit_price: 0, gst: 0, amount: 0 }],
      });
    }
  }, [voucherData, mode, reset]);

  const createMutation = useMutation((data: any) => voucherService.createPurchaseOrder(data), {
    onSuccess: () => {
      queryClient.invalidateQueries('purchaseOrders');
      setMode('create');
      setSelectedId(null);
    },
    onError: (error: any) => {
      alert(error.userMessage || 'Failed to create voucher');
    }
  });

  const updateMutation = useMutation((data: any) => voucherService.updatePurchaseOrder(selectedId!, data), {
    onSuccess: () => {
      queryClient.invalidateQueries('purchaseOrders');
      setMode('view');
    },
    onError: (error: any) => {
      alert(error.userMessage || 'Failed to update voucher');
    }
  });

  const onSubmit = (data: any) => {
    if (mode === 'create') {
      createMutation.mutate(data);
    } else if (mode === 'edit') {
      updateMutation.mutate(data);
    }
  };

  const handleNew = () => {
    setMode('create');
    setSelectedId(null);
  };

  const handleEdit = (voucherId: number) => {
    setSelectedId(voucherId);
    setMode('edit');
    router.push({ query: { id: voucherId, mode: 'edit' } }, undefined, { shallow: true });
  };

  const handleView = (voucherId: number) => {
    setSelectedId(voucherId);
    setMode('view');
    router.push({ query: { id: voucherId, mode: 'view' } }, undefined, { shallow: true });
  };

  if (isLoadingList || isFetching) {
    return <CircularProgress />;
  }

  const isViewMode = mode === 'view';

  return (
    <Container maxWidth="xl">
      <Grid container spacing={2}>
        <Grid item xs={12} md={5} lg={4.8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Purchase Orders
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Voucher #</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Vendor</TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {voucherList?.map((voucher: any) => (
                    <TableRow key={voucher.id}>
                      <TableCell>{voucher.voucher_number}</TableCell>
                      <TableCell>{new Date(voucher.date).toLocaleDateString()}</TableCell>
                      <TableCell>{voucher.vendor}</TableCell>
                      <TableCell>
                        <IconButton onClick={() => handleView(voucher.id)}>
                          <Visibility />
                        </IconButton>
                        <IconButton onClick={() => handleEdit(voucher.id)}>
                          <Edit />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={7} lg={7.2}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h4" gutterBottom>
              {mode === 'create' ? 'Create' : mode === 'edit' ? 'Edit' : 'View'} Purchase Order
            </Typography>
            <form onSubmit={handleSubmit(onSubmit)}>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="Voucher Number"
                    {...control.register('voucher_number', { required: true })}
                    error={!!errors.voucher_number}
                    helperText={errors.voucher_number ? 'Required' : ''}
                    disabled={isViewMode}
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="Date"
                    type="date"
                    {...control.register('date', { required: true })}
                    error={!!errors.date}
                    helperText={errors.date ? 'Required' : ''}
                    disabled={isViewMode}
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="Required by Date"
                    type="date"
                    {...control.register('required_by_date', { required: true })}
                    error={!!errors.required_by_date}
                    helperText={errors.required_by_date ? 'Required' : ''}
                    disabled={isViewMode}
                  />
                </Grid>
                <Grid item xs={6}>
                  <SearchableDropdown
                    options={vendorList || []}
                    value={watch('vendor')}
                    onChange={(value) => setValue('vendor', value)}
                    onAddNew={() => setAddVendorDialogOpen(true)}
                    getOptionLabel={(option) => option.name}
                    getOptionValue={(option) => option.id}
                    label="Vendor"
                    placeholder="Search vendors..."
                    disabled={isViewMode}
                    error={!!errors.vendor}
                    helperText={errors.vendor ? 'Required' : ''}
                    required={true}
                    addNewText="Add New Vendor"
                    searchFields={['name', 'email', 'contact_number']}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Payment Terms"
                    {...control.register('payment_terms')}
                    disabled={isViewMode}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="h6">Items</Typography>
                  {fields.map((field, index) => (
                    <Grid container spacing={2} key={field.id} sx={{ mb: 2 }}>
                      <Grid item xs={3}>
                        <SearchableDropdown
                          options={productList || []}
                          value={watch(`items.${index}.name`)}
                          onChange={(value) => {
                            setValue(`items.${index}.name`, value);
                            // Auto-fill product details when selected
                            const selectedProduct = productList?.find((p: any) => p.id === value);
                            if (selectedProduct) {
                              setValue(`items.${index}.hsn_code`, selectedProduct.hsn_code || '');
                              setValue(`items.${index}.unit`, selectedProduct.unit || '');
                              setValue(`items.${index}.unit_price`, selectedProduct.unit_price || 0);
                              setValue(`items.${index}.gst`, selectedProduct.gst_rate || 0);
                            }
                          }}
                          onAddNew={() => setAddProductDialogOpen(true)}
                          getOptionLabel={(option) => option.name}
                          getOptionValue={(option) => option.id}
                          label="Product"
                          placeholder="Search products..."
                          disabled={isViewMode}
                          error={!!errors.items?.[index]?.name}
                          helperText={errors.items?.[index]?.name ? 'Required' : ''}
                          required={true}
                          addNewText="Add New Product"
                          searchFields={['name', 'hsn_code', 'part_number']}
                        />
                      </Grid>
                      <Grid item xs={2}>
                        <TextField
                          fullWidth
                          label="HSN Code"
                          {...control.register(`items.${index}.hsn_code`)}
                          disabled={isViewMode}
                        />
                      </Grid>
                      <Grid item xs={1}>
                        <TextField
                          fullWidth
                          label="Qty"
                          type="number"
                          {...control.register(`items.${index}.quantity`, { required: true, valueAsNumber: true })}
                          error={!!errors.items?.[index]?.quantity}
                          helperText={errors.items?.[index]?.quantity ? 'Required' : ''}
                          disabled={isViewMode}
                        />
                      </Grid>
                      <Grid item xs={1}>
                        <TextField
                          fullWidth
                          label="Unit"
                          {...control.register(`items.${index}.unit`, { required: true })}
                          error={!!errors.items?.[index]?.unit}
                          helperText={errors.items?.[index]?.unit ? 'Required' : ''}
                          disabled={isViewMode}
                        />
                      </Grid>
                      <Grid item xs={1.5}>
                        <TextField
                          fullWidth
                          label="Unit Price"
                          type="number"
                          {...control.register(`items.${index}.unit_price`, { required: true, valueAsNumber: true })}
                          error={!!errors.items?.[index]?.unit_price}
                          helperText={errors.items?.[index]?.unit_price ? 'Required' : ''}
                          disabled={isViewMode}
                        />
                      </Grid>
                      <Grid item xs={1}>
                        <TextField
                          fullWidth
                          label="GST %"
                          type="number"
                          {...control.register(`items.${index}.gst`, { valueAsNumber: true })}
                          disabled={isViewMode}
                        />
                      </Grid>
                      <Grid item xs={1.5}>
                        <TextField
                          fullWidth
                          label="Amount"
                          type="number"
                          value={watch(`items.${index}.amount`)}
                          disabled
                        />
                      </Grid>
                      {!isViewMode && (
                        <Grid item xs={0.5}>
                          <IconButton sx={{ backgroundColor: 'error.main', color: 'white' }} onClick={() => remove(index)} disabled={fields.length === 1}>
                            <Remove />
                          </IconButton>
                        </Grid>
                      )}
                    </Grid>
                  ))}
                  {!isViewMode && (
                    <Box sx={{ mb: 2 }}>
                      <Typography sx={{ color: 'success.main', cursor: 'pointer' }} onClick={() => append({ name: '', hsn_code: '', quantity: 0, unit: '', unit_price: 0, gst: 0, amount: 0 })}>
                        Add Item
                      </Typography>
                    </Box>
                  )}
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Total Amount"
                    type="number"
                    value={totalAmount}
                    disabled
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Amount in Words"
                    value={numberToWords(totalAmount || 0)}
                    disabled
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Notes"
                    multiline
                    rows={4}
                    {...control.register('notes')}
                    disabled={isViewMode}
                  />
                </Grid>
              </Grid>
              <Box sx={{ mt: 2 }}>
                {!isViewMode && (
                  <Button type="submit" variant="contained" color="success" disabled={createMutation.isLoading || updateMutation.isLoading} sx={{ mr: 2 }}>
                    Save
                  </Button>
                )}
                <Button variant="contained" color="error" onClick={() => router.push('/dashboard')} sx={{ mr: 2 }}>
                  Cancel
                </Button>
                <Button variant="contained" color="primary">
                  Manage Column
                </Button>
              </Box>
            </form>
          </Paper>
        </Grid>
      </Grid>

      {/* Add Vendor Dialog */}
      <Dialog
        open={addVendorDialogOpen}
        onClose={() => setAddVendorDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add New Vendor</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            You can create a new vendor by going to the vendor management page, or continue with the current flow.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddVendorDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={() => {
              setAddVendorDialogOpen(false);
              router.push('/masters/vendors');
            }}
          >
            Go to Vendors
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Product Dialog */}
      <Dialog
        open={addProductDialogOpen}
        onClose={() => setAddProductDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add New Product</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            You can create a new product by going to the product management page, or continue with the current flow.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddProductDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={() => {
              setAddProductDialogOpen(false);
              router.push('/masters/products');
            }}
          >
            Go to Products
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default PurchaseOrderPage;