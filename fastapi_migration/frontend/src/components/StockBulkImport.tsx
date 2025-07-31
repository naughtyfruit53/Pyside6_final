import React, { useState } from 'react';
import { Button, Box, Typography, Input } from '@mui/material';
import { masterDataService } from '../services/authService'; // Import the service

const StockBulkImport = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setError('Please select an Excel file to upload.');
      return;
    }

    try {
      const res = await masterDataService.bulkImportStock(selectedFile);
      setResponse(res);
      setError(null);
    } catch (err) {
      setError(err.userMessage || 'Failed to import Excel file. Check the file format and try again.');
      setResponse(null);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6">Bulk Import Stock from Excel</Typography>
      <Input
        type="file"
        onChange={handleFileChange}
        inputProps={{ accept: '.xlsx, .xls' }}
        sx={{ mb: 2 }}
      />
      <Button variant="contained" onClick={handleSubmit}>Import</Button>
      {response && <pre>{JSON.stringify(response, null, 2)}</pre>}
      {error && <Typography color="error">{error}</Typography>}
    </Box>
  );
};

export default StockBulkImport;