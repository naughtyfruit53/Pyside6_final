// fastapi_migration/frontend/src/components/OrganizationForm.tsx

import React from 'react';
import { useForm } from 'react-hook-form';
import { Button, TextField } from '@mui/material';

interface OrganizationFormProps {
  onSubmit: (data: any) => void;
  defaultValues?: any;
}

const OrganizationForm: React.FC<OrganizationFormProps> = ({ onSubmit, defaultValues = {} }) => {
  const { register, handleSubmit } = useForm({ defaultValues });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <TextField label="Name" {...register('name', { required: true })} fullWidth margin="normal" />
      {/* Add more fields as needed */}
      <Button type="submit" variant="contained" color="primary">
        Submit
      </Button>
    </form>
  );
};

export default OrganizationForm;