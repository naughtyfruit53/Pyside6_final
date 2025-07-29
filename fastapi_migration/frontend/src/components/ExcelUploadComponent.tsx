import React, { useState } from 'react';
import { Button, Typography, CircularProgress, Alert, Box } from '@mui/material';
import axios from 'axios';

const ExcelUploadComponent = ({ endpoint = '/api/v1/stock/import/excel' }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setResponse(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select an Excel file first');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${localStorage.getItem('token')}`,  // Assume token-based auth
        },
      });
      setResponse(res.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
      setResponse(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6">Upload Excel File</Typography>
      <input type="file" accept=".xlsx,.xls" onChange={handleFileChange} />
      <Button variant="contained" onClick={handleUpload} disabled={loading} sx={{ mt: 2 }}>
        {loading ? <CircularProgress size={24} /> : 'Upload'}
      </Button>
      {response && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {response.message} (Processed: {response.total_processed}, Errors: {response.errors.length})
        </Alert>
      )}
      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
    </Box>
  );
};

export default ExcelUploadComponent;