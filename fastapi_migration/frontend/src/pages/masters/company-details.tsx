import React, { useState } from 'react';
import { Box, Paper, Typography, Grid, Button, Alert } from '@mui/material';
import { Edit } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { companyService } from '../../services/authService';
import CompanyDetailsModal from '../../components/CompanyDetailsModal';

const CompanyDetails: React.FC = () => {
  const [openModal, setOpenModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: company, isLoading, isError } = useQuery('company', companyService.getCurrentCompany, {
    onError: () => console.error('Failed to fetch company details'),
  });

  const mutation = useMutation(companyService.createCompany, {
    onSuccess: () => {
      queryClient.invalidateQueries('company');
    },
  });

  const handleOpenModal = () => setOpenModal(true);
  const handleCloseModal = () => setOpenModal(false);
  const handleSuccess = () => {
    queryClient.invalidateQueries('company');
    handleCloseModal();
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  if (isError || !company) {
    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Company Details
        </Typography>
        <Alert severity="info">
          No company details found. Please set up your company information.
        </Alert>
        <Button
          variant="contained"
          startIcon={<Edit />}
          sx={{ mt: 3 }}
          onClick={handleOpenModal}
        >
          Set Up Company Details
        </Button>
        <CompanyDetailsModal 
          open={openModal} 
          onClose={handleCloseModal} 
          onSuccess={handleSuccess}
          isRequired={false}
        />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Company Details
      </Typography>
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
            <Typography variant="subtitle2">GST Number</Typography>
            <Typography>{company.gst_number}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2">PAN Number</Typography>
            <Typography>{company.pan_number}</Typography>
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
              {company.address1}{company.address2 ? `, ${company.address2}` : ''}, {company.city}, {company.state} {company.pin_code}
            </Typography>
          </Grid>
        </Grid>
        <Button
          variant="contained"
          startIcon={<Edit />}
          sx={{ mt: 3 }}
          onClick={handleOpenModal}
        >
          Edit Company Details
        </Button>
      </Paper>
      <CompanyDetailsModal 
        open={openModal} 
        onClose={handleCloseModal} 
        onSuccess={handleSuccess}
        isRequired={false}
      />
    </Box>
  );
};

export default CompanyDetails;