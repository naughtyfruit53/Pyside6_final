// components/ExcelImportExport.tsx
'use client';

import React from 'react';
import { Button, Box } from '@mui/material';
import { exportToExcel, importFromExcel } from '../lib/excelUtils';

interface ExcelImportExportProps {
  data: any[];
  entity: string;
  onImport: (importedData: any[]) => void;
}

const ExcelImportExport: React.FC<ExcelImportExportProps> = ({ data, entity, onImport }) => {
  const handleExport = () => {
    exportToExcel(data, entity);
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const importedData = await importFromExcel(file);
      onImport(importedData);
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
      <Button variant="outlined" onClick={handleExport}>
        Export {entity} to Excel
      </Button>
      <Button variant="outlined" component="label">
        Import {entity} from Excel
        <input type="file" hidden accept=".xlsx" onChange={handleImport} />
      </Button>
    </Box>
  );
};

export default ExcelImportExport;