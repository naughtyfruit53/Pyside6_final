// ProductDropdown component using name field as specified
import React, { useState, useEffect } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  CircularProgress,
  Box,
  TextField,
  Autocomplete
} from '@mui/material';

export interface Product {
  id: number;
  product_name: string;  // Using product_name field for frontend consistency as per requirements
  hsn_code?: string;
  part_number?: string;
  unit: string;
  unit_price: number;
  gst_rate: number;
  is_gst_inclusive: boolean;
  reorder_level: number;
  description?: string;
  is_manufactured: boolean;
  organization_id: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

interface ProductDropdownProps {
  value?: number;
  onChange: (productId: number, product: Product | null) => void;
  label?: string;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
  required?: boolean;
  fullWidth?: boolean;
  variant?: 'autocomplete' | 'select';
  placeholder?: string;
  showDetails?: boolean;
}

const ProductDropdown: React.FC<ProductDropdownProps> = ({
  value,
  onChange,
  label = 'Select Product',
  disabled = false,
  error = false,
  helperText,
  required = false,
  fullWidth = true,
  variant = 'autocomplete',
  placeholder = 'Search products...',
  showDetails = false
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async (search?: string) => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      if (search) {
        queryParams.append('search', search);
      }
      queryParams.append('active_only', 'true');
      queryParams.append('limit', '100');

      const response = await fetch(`/api/v1/products?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch products');
      }

      const data = await response.json();
      setProducts(data);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (productId: number) => {
    const selectedProduct = products.find(p => p.id === productId) || null;
    onChange(productId, selectedProduct);
  };

  const selectedProduct = products.find(p => p.id === value);

  if (variant === 'autocomplete') {
    return (
      <Autocomplete
        fullWidth={fullWidth}
        value={selectedProduct || null}
        onChange={(_, newValue) => {
          if (newValue) {
            handleChange(newValue.id);
          } else {
            onChange(0, null);
          }
        }}
        options={products}
        getOptionLabel={(option) => option.product_name}
        renderOption={(props, option) => (
          <li {...props}>
            <Box>
              <div>{option.product_name}</div>
              {showDetails && (
                <div style={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                  {option.hsn_code && `HSN: ${option.hsn_code} • `}
                  {option.part_number && `PN: ${option.part_number} • `}
                  Unit: {option.unit} • ₹{option.unit_price}
                </div>
              )}
            </Box>
          </li>
        )}
        renderInput={(params) => (
          <TextField
            {...params}
            label={label}
            placeholder={placeholder}
            required={required}
            error={error}
            helperText={helperText}
            disabled={disabled}
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <>
                  {loading ? <CircularProgress color="inherit" size={20} /> : null}
                  {params.InputProps.endAdornment}
                </>
              ),
            }}
          />
        )}
        loading={loading}
        disabled={disabled}
        noOptionsText="No products found"
        isOptionEqualToValue={(option, value) => option.id === value.id}
      />
    );
  }

  // Select variant
  return (
    <FormControl 
      fullWidth={fullWidth} 
      error={error} 
      disabled={disabled}
      required={required}
    >
      <InputLabel>{label}</InputLabel>
      <Select
        value={value || ''}
        onChange={(e: SelectChangeEvent<number>) => {
          const productId = e.target.value as number;
          handleChange(productId);
        }}
        label={label}
        disabled={disabled}
      >
        <MenuItem value="">
          <em>None</em>
        </MenuItem>
        {loading ? (
          <MenuItem disabled>
            <CircularProgress size={20} />
            <Box ml={1}>Loading products...</Box>
          </MenuItem>
        ) : (
          products.map((product) => (
            <MenuItem key={product.id} value={product.id}>
              {product.product_name}
              {showDetails && (
                <Box component="span" sx={{ fontSize: '0.75rem', color: 'text.secondary', ml: 1 }}>
                  ({product.unit} • ₹{product.unit_price})
                </Box>
              )}
            </MenuItem>
          ))
        )}
      </Select>
      {helperText && (
        <Box sx={{ fontSize: '0.75rem', color: error ? 'error.main' : 'text.secondary', mt: 0.5 }}>
          {helperText}
        </Box>
      )}
    </FormControl>
  );
};

export default ProductDropdown;