// SortableTable component for requirement #3 - Table Sorting on Header Click
import React, { useState, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Box,
  Typography
} from '@mui/material';
import { visuallyHidden } from '@mui/utils';

export type Order = 'asc' | 'desc';

export interface HeadCell<T> {
  id: keyof T;
  label: string;
  numeric: boolean;
  disablePadding?: boolean;
  sortable?: boolean;
  width?: string | number;
  align?: 'left' | 'right' | 'center';
  render?: (value: any, row: T) => React.ReactNode;
}

interface SortableTableProps<T> {
  data: T[];
  headCells: HeadCell<T>[];
  title?: string;
  defaultOrderBy?: keyof T;
  defaultOrder?: Order;
  onRowClick?: (row: T) => void;
  dense?: boolean;
  stickyHeader?: boolean;
  maxHeight?: string | number;
  emptyMessage?: string;
  loading?: boolean;
  actions?: (row: T) => React.ReactNode;
}

function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  const aVal = a[orderBy];
  const bVal = b[orderBy];
  
  // Handle null/undefined values
  if (bVal == null && aVal == null) return 0;
  if (bVal == null) return -1;
  if (aVal == null) return 1;
  
  // Handle different types
  if (typeof aVal === 'number' && typeof bVal === 'number') {
    return bVal - aVal;
  }
  
  if (typeof aVal === 'string' && typeof bVal === 'string') {
    return bVal.localeCompare(aVal, undefined, { numeric: true, sensitivity: 'base' });
  }
  
  // Handle dates
  if (aVal instanceof Date && bVal instanceof Date) {
    return bVal.getTime() - aVal.getTime();
  }
  
  // Handle date strings
  if (typeof aVal === 'string' && typeof bVal === 'string') {
    const aDate = new Date(aVal);
    const bDate = new Date(bVal);
    if (!isNaN(aDate.getTime()) && !isNaN(bDate.getTime())) {
      return bDate.getTime() - aDate.getTime();
    }
  }
  
  // Default string comparison
  return String(bVal).localeCompare(String(aVal), undefined, { numeric: true, sensitivity: 'base' });
}

function getComparator<T>(order: Order, orderBy: keyof T): (a: T, b: T) => number {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

function stableSort<T>(array: readonly T[], comparator: (a: T, b: T) => number) {
  const stabilizedThis = array.map((el, index) => [el, index] as [T, number]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) {
      return order;
    }
    return a[1] - b[1];
  });
  return stabilizedThis.map((el) => el[0]);
}

interface SortableTableHeadProps<T> {
  headCells: HeadCell<T>[];
  order: Order;
  orderBy: keyof T;
  onRequestSort: (property: keyof T) => void;
  hasActions: boolean;
}

function SortableTableHead<T>(props: SortableTableHeadProps<T>) {
  const { headCells, order, orderBy, onRequestSort, hasActions } = props;
  
  const createSortHandler = (property: keyof T) => () => {
    onRequestSort(property);
  };

  return (
    <TableHead>
      <TableRow>
        {headCells.map((headCell) => (
          <TableCell
            key={String(headCell.id)}
            align={headCell.align || (headCell.numeric ? 'right' : 'left')}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
            sx={{ 
              fontWeight: 'bold',
              width: headCell.width,
              backgroundColor: 'grey.50'
            }}
          >
            {headCell.sortable !== false ? (
              <TableSortLabel
                active={orderBy === headCell.id}
                direction={orderBy === headCell.id ? order : 'asc'}
                onClick={createSortHandler(headCell.id)}
              >
                {headCell.label}
                {orderBy === headCell.id ? (
                  <Box component="span" sx={visuallyHidden}>
                    {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                  </Box>
                ) : null}
              </TableSortLabel>
            ) : (
              headCell.label
            )}
          </TableCell>
        ))}
        {hasActions && (
          <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: 'grey.50' }}>
            Actions
          </TableCell>
        )}
      </TableRow>
    </TableHead>
  );
}

function SortableTable<T>({
  data,
  headCells,
  title,
  defaultOrderBy,
  defaultOrder = 'asc',
  onRowClick,
  dense = false,
  stickyHeader = false,
  maxHeight,
  emptyMessage = 'No data available',
  loading = false,
  actions
}: SortableTableProps<T>) {
  const [order, setOrder] = useState<Order>(defaultOrder);
  const [orderBy, setOrderBy] = useState<keyof T>(defaultOrderBy || headCells[0]?.id);

  const handleRequestSort = (property: keyof T) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedData = useMemo(() => {
    if (!data?.length) return [];
    return stableSort(data, getComparator(order, orderBy));
  }, [data, order, orderBy]);

  const hasActions = Boolean(actions);

  if (loading) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Loading...</Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ width: '100%', mb: 2 }}>
      {title && (
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" component="div">
            {title}
          </Typography>
        </Box>
      )}
      <TableContainer sx={{ maxHeight }}>
        <Table
          stickyHeader={stickyHeader}
          size={dense ? 'small' : 'medium'}
          aria-label="sortable table"
        >
          <SortableTableHead
            headCells={headCells}
            order={order}
            orderBy={orderBy}
            onRequestSort={handleRequestSort}
            hasActions={hasActions}
          />
          <TableBody>
            {sortedData.length === 0 ? (
              <TableRow>
                <TableCell 
                  colSpan={headCells.length + (hasActions ? 1 : 0)} 
                  align="center"
                  sx={{ py: 3 }}
                >
                  <Typography color="textSecondary">
                    {emptyMessage}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              sortedData.map((row, index) => (
                <TableRow
                  hover={Boolean(onRowClick)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  key={index}
                  sx={{ 
                    cursor: onRowClick ? 'pointer' : 'default',
                    '&:hover': onRowClick ? { backgroundColor: 'action.hover' } : {}
                  }}
                >
                  {headCells.map((headCell) => (
                    <TableCell
                      key={String(headCell.id)}
                      align={headCell.align || (headCell.numeric ? 'right' : 'left')}
                      padding={headCell.disablePadding ? 'none' : 'normal'}
                    >
                      {headCell.render 
                        ? headCell.render(row[headCell.id], row)
                        : String(row[headCell.id] ?? '')
                      }
                    </TableCell>
                  ))}
                  {hasActions && (
                    <TableCell align="center">
                      {actions(row)}
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}

export default SortableTable;