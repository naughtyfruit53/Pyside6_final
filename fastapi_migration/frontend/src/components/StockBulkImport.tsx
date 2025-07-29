import React, { useState } from 'react';
import { Button, TextField, Box, Typography } from '@mui/material';
import axios from 'axios';

const StockBulkImport = () => {
  const [stockItems, setStockItems] = useState('');  // Textarea for JSON input
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    try {
      const itemsArray = JSON.parse(stockItems);  // Parse user input as array
      if (!Array.isArray(itemsArray)) {
        throw new Error('Input must be a JSON array');
      }
      const payload = { items: itemsArray };  // Wrap in { items: [...] }
      const res = await axios.post('/api/v1/stock/bulk', payload);
      setResponse(res.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid request - ensure body is { "items": [...] }');
      setResponse(null);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6">Bulk Import Stock</Typography>
      <TextField
        multiline
        rows={10}
        fullWidth
        label="Enter JSON Array of Stock Items"
        value={stockItems}
        onChange={(e) => setStockItems(e.target.value)}
        placeholder='[{"product_name": "Item1", "unit": "PCS", "quantity": 10.0}, ...]'
        sx={{ mb: 2 }}
      />
      <Button variant="contained" onClick={handleSubmit}>Import</Button>
      {response && <pre>{JSON.stringify(response, null, 2)}</pre>}
      {error && <Typography color="error">{error}</Typography>}
    </Box>
  );
};

export default StockBulkImport;