// purchase-voucher.tsx
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { Box, Button, TextField, Typography, Grid, IconButton, Alert, CircularProgress, Container, Checkbox, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Select, MenuItem } from '@mui/material';
import { Add, Remove, Edit, Visibility } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { voucherService } from '../../../services/authService';
import { getVendors, getProducts } from '../../../services/masterService';

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

const PurchaseVoucherPage: React.FC = () => {
  const router = useRouter();
  const { id, mode: queryMode } = router.query;
  const [mode, setMode ] = useState<'create' | 'edit' | 'view'>((queryMode as any) || 'create');
  const [selectedId, setSelectedId] = useState<number | null>(id ? Number(id) : null);
  const queryClient = useQueryClient();

  const { control, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm({
    defaultValues: {
      voucher_number: 'PV/2526/00000001',
      date: new Date().toISOString().slice(0, 10),
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
    ['purchaseVouchers'],
    () => voucherService.getPurchaseVouchers() // Assume this method exists
  );

  const { data: vendorList } = useQuery(
    ['vendors'],
    () => getVendors()
  );

  const { data: productList } = useQuery(
    ['products'],
    () => getProducts()
  );

  const { data: voucherData, isLoading: isFetching } = useQuery(
    ['purchaseVoucher', selectedId],
    () => voucherService.getPurchaseVoucherById(selectedId!),
    { enabled: !!selectedId }
  );

  useEffect(() => {
    if (voucherData) {
      reset(voucherData);
    } else if (mode === 'create') {
      reset({
        voucher_number: 'PV/2526/00000001',
        date: new Date().toISOString().slice(0, 10),
        vendor: '',
        payment_terms: '',
        total_amount: 0,
        notes: '',
        items: [{ name: '', hsn_code: '', quantity: 0, unit: '', unit_price: 0, gst: 0, amount: 0 }],
      });
    }
  }, [voucherData, mode, reset]);

  const createMutation = useMutation((data: any) => voucherService.createPurchaseVoucher(data), {
    onSuccess: () => {
      queryClient.invalidateQueries('purchaseVouchers');
      setMode('create');
      setSelectedId(null);
    },
    onError: (error: any) => {
      alert(error.userMessage || 'Failed to create voucher');
    }
  });

  const updateMutation = useMutation((data: any) => voucherService.updatePurchaseVoucher(selectedId!, data), {
    onSuccess: () => {
      queryClient.invalidateQueries('purchaseVouchers');
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

  // Handle adding new vendor from voucher form
  const handleAddVendor = () => {
    // Open vendor add dialog (navigate to masters with vendor tab and add mode)
    window.open('/masters?tab=vendors&action=add', '_blank', 'width=800,height=600');
    // Alternatively, you could implement a modal dialog here
  };

  // Handle adding new product from voucher form
  const handleAddProduct = () => {
    // Open product add dialog (navigate to masters with product tab and add mode)
    window.open('/masters?tab=products&action=add', '_blank', 'width=800,height=600');
    // Alternatively, you could implement a modal dialog here
  };

  // Refresh vendor and product lists (called when add dialogs are closed)
  const refreshMasterData = () => {
    queryClient.invalidateQueries('vendors');
    queryClient.invalidateQueries('products');
  };

  // Listen for storage events to refresh data when new items are added
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'refreshMasterData') {
        refreshMasterData();
        localStorage.removeItem('refreshMasterData');
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [queryClient]);

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
              Purchase Vouchers
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
              {mode === 'create' ? 'Create' : mode === 'edit' ? 'Edit' : 'View'} Purchase Voucher
            </Typography>
            <form onSubmit={handleSubmit(onSubmit)}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Voucher Number"
                    {...control.register('voucher_number', { required: true })}
                    error={!!errors.voucher_number}
                    helperText={errors.voucher_number ? 'Required' : ''}
                    disabled={isViewMode}
                  />
                </Grid>
                <Grid item xs={6}>
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
                <Grid item xs={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Select
                      fullWidth
                      {...control.register('vendor', { required: true })}
                      error={!!errors.vendor}
                      disabled={isViewMode}
                      displayEmpty
                    >
                      <MenuItem value="" disabled>Select Vendor</MenuItem>
                      {vendorList?.map((vendor: any) => (
                        <MenuItem key={vendor.id} value={vendor.id}>{vendor.name}</MenuItem>
                      ))}
                    </Select>
                    {!isViewMode && (
                      <Button
                        variant="outlined"
                        startIcon={<Add />}
                        onClick={handleAddVendor}
                        sx={{ minWidth: 100 }}
                      >
                        Add Vendor
                      </Button>
                    )}
                  </Box>
                  {errors.vendor && <Typography color="error" variant="caption">Required</Typography>}
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
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Select
                            fullWidth
                            {...control.register(`items.${index}.name`, { required: true })}
                            error={!!errors.items?.[index]?.name}
                            disabled={isViewMode}
                            displayEmpty
                          >
                            <MenuItem value="" disabled>Select Product</MenuItem>
                            {productList?.map((product: any) => (
                              <MenuItem key={product.id} value={product.product_name}>{product.product_name}</MenuItem>
                            ))}
                          </Select>
                          {!isViewMode && index === 0 && (
                            <Button
                              variant="outlined"
                              startIcon={<Add />}
                              onClick={handleAddProduct}
                              sx={{ minWidth: 80, fontSize: '0.75rem' }}
                              size="small"
                            >
                              Add
                            </Button>
                          )}
                        </Box>
                        {errors.items?.[index]?.name && <Typography color="error" variant="caption">Required</Typography>}
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
                      <Typography sx={{ color: 'green', cursor: 'pointer' }} onClick={() => append({ name: '', hsn_code: '', quantity: 0, unit: '', unit_price: 0, gst: 0, amount: 0 })}>
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
    </Container>
  );
};

export default PurchaseVoucherPage;