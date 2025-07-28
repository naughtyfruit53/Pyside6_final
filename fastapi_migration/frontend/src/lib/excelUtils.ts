// lib/excelUtils.ts
import ExcelJS from 'exceljs';  // New library for creating/reading Excel files
import saveAs from 'file-saver';  // Library to handle file downloads in the browser

// Function to export data (array of objects) to an Excel file
export const exportToExcel = async (data: any[], filename: string) => {
  // Create a new Excel workbook
  const workbook = new ExcelJS.Workbook();
  // Add a worksheet to it
  const worksheet = workbook.addWorksheet('Sheet1');

  // If there's data, add headers (column names) as the first row
  if (data.length > 0) {
    worksheet.addRow(Object.keys(data[0]));  // e.g., ['id', 'name', 'price']
    // Then add each row of data
    data.forEach(item => {
      worksheet.addRow(Object.values(item));  // e.g., [1, 'Product A', 10.99]
    });
  }

  // Generate the Excel file as a buffer (binary data)
  const buffer = await workbook.xlsx.writeBuffer();
  // Create a Blob (file-like object) from the buffer
  const blob = new Blob([buffer], { type: 'application/octet-stream' });
  // Trigger download with the given filename
  saveAs(blob, `${filename}.xlsx`);
};

// Function to import data from an uploaded Excel file
export const importFromExcel = async (file: File): Promise<any[]> => {
  // Create a new workbook
  const workbook = new ExcelJS.Workbook();
  // Read the file's contents into a buffer
  const buffer = await file.arrayBuffer();
  // Load the buffer into the workbook
  await workbook.xlsx.load(buffer);
  // Get the first worksheet
  const worksheet = workbook.getWorksheet(1);
  const json: any[] = [];
  // Get headers from the first row
  const headers = worksheet.getRow(1).values as string[];

  // Loop through each row (skip header row)
  worksheet.eachRow({ includeEmpty: false }, (row, rowNumber) => {
    if (rowNumber > 1) {
      const rowData: { [key: string]: any } = {};
      // Loop through each cell in the row
      row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
        if (headers[colNumber]) {
          rowData[headers[colNumber]] = cell.value;  // Map cell value to header key
        }
      });
      json.push(rowData);  // Add the row object to the result array
    }
  });

  return json;  // Return array of objects (e.g., [{id:1, name:'Product A'}, ...])
};