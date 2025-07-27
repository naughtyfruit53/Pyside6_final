// fastapi_migration/frontend/src/components/OrganizationList.tsx

import React from 'react';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Button } from '@mui/material';
import Link from 'next/link';

interface OrganizationListProps {
  organizations: any[];
  onRefresh: () => void;
}

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 90 },
  { field: 'name', headerName: 'Name', width: 200 },
  {
    field: 'actions',
    headerName: 'Actions',
    width: 150,
    renderCell: (params) => (
      <Link href={`/admin/organizations/edit/${params.row.id}`}>
        <Button variant="outlined" size="small">Edit</Button>
      </Link>
    ),
  },
];

const OrganizationList: React.FC<OrganizationListProps> = ({ organizations, onRefresh }) => {
  return (
    <div style={{ height: 400, width: '100%' }}>
      <DataGrid rows={organizations} columns={columns} />
      <Button onClick={onRefresh} variant="contained" color="primary" style={{ marginTop: 16 }}>
        Refresh
      </Button>
    </div>
  );
};

export default OrganizationList;