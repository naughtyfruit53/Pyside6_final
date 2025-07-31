import React, { useState, useEffect } from 'react';
import {
  Autocomplete,
  TextField,
  Button,
  Box,
  Typography,
  Paper,
  Popper,
  ClickAwayListener,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import { Add, Search } from '@mui/icons-material';

interface SearchableDropdownProps {
  options: any[];
  value: any;
  onChange: (value: any) => void;
  onAddNew?: () => void;
  getOptionLabel: (option: any) => string;
  getOptionValue: (option: any) => any;
  placeholder?: string;
  label?: string;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
  required?: boolean;
  noOptionsText?: string;
  addNewText?: string;
  searchFields?: string[]; // Fields to search in (e.g., ['name', 'email'])
  fullWidth?: boolean;
}

const SearchableDropdown: React.FC<SearchableDropdownProps> = ({
  options = [],
  value,
  onChange,
  onAddNew,
  getOptionLabel,
  getOptionValue,
  placeholder = "Search...",
  label,
  disabled = false,
  error = false,
  helperText,
  required = false,
  noOptionsText = "No options found",
  addNewText = "Add New",
  searchFields = ['name'],
  fullWidth = true
}) => {
  const [inputValue, setInputValue] = useState('');
  const [filteredOptions, setFilteredOptions] = useState(options);
  const [showAddNew, setShowAddNew] = useState(false);

  // Filter options based on input value
  useEffect(() => {
    if (!inputValue.trim()) {
      setFilteredOptions(options);
      setShowAddNew(false);
      return;
    }

    const filtered = options.filter(option => {
      const searchTerm = inputValue.toLowerCase();
      return searchFields.some(field => {
        const fieldValue = option[field]?.toString().toLowerCase() || '';
        return fieldValue.includes(searchTerm);
      });
    });

    setFilteredOptions(filtered);
    
    // Show "Add New" option if no results found and onAddNew is provided
    setShowAddNew(filtered.length === 0 && onAddNew && inputValue.trim().length > 0);
  }, [inputValue, options, searchFields, onAddNew]);

  const handleOptionSelect = (option: any) => {
    onChange(getOptionValue(option));
    setInputValue(getOptionLabel(option));
  };

  const handleAddNew = () => {
    if (onAddNew) {
      onAddNew();
    }
  };

  const CustomPopper = (props: any) => {
    return (
      <Popper {...props} style={{ width: props.anchorEl?.clientWidth || 'auto' }} placement="bottom-start">
        <Paper elevation={3} sx={{ maxHeight: 300, overflow: 'auto' }}>
          <List dense>
            {filteredOptions.map((option, index) => (
              <ListItem
                key={index}
                button
                onClick={() => handleOptionSelect(option)}
                sx={{
                  '&:hover': {
                    backgroundColor: 'action.hover'
                  }
                }}
              >
                <ListItemText
                  primary={getOptionLabel(option)}
                  secondary={option.email || option.code || option.description || ''}
                />
              </ListItem>
            ))}
            
            {filteredOptions.length === 0 && !showAddNew && (
              <ListItem>
                <ListItemText
                  primary={noOptionsText}
                  sx={{ color: 'text.secondary', fontStyle: 'italic' }}
                />
              </ListItem>
            )}
            
            {showAddNew && (
              <>
                {filteredOptions.length > 0 && <Divider />}
                <ListItem
                  button
                  onClick={handleAddNew}
                  sx={{
                    backgroundColor: 'primary.light',
                    color: 'primary.contrastText',
                    '&:hover': {
                      backgroundColor: 'primary.main'
                    }
                  }}
                >
                  <ListItemIcon sx={{ color: 'inherit' }}>
                    <Add />
                  </ListItemIcon>
                  <ListItemText
                    primary={`${addNewText} "${inputValue}"`}
                    sx={{ fontWeight: 'medium' }}
                  />
                </ListItem>
              </>
            )}
          </List>
        </Paper>
      </Popper>
    );
  };

  return (
    <Autocomplete
      fullWidth={fullWidth}
      options={filteredOptions}
      getOptionLabel={getOptionLabel}
      value={value ? options.find(option => getOptionValue(option) === value) || null : null}
      onChange={(event, newValue) => {
        if (newValue) {
          onChange(getOptionValue(newValue));
        } else {
          onChange(null);
        }
      }}
      inputValue={inputValue}
      onInputChange={(event, newInputValue) => {
        setInputValue(newInputValue);
      }}
      disabled={disabled}
      noOptionsText={
        showAddNew ? (
          <Box>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
              {noOptionsText}
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleAddNew}
              size="small"
              fullWidth
            >
              {addNewText} "{inputValue}"
            </Button>
          </Box>
        ) : (
          noOptionsText
        )
      }
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          placeholder={placeholder}
          error={error}
          helperText={helperText}
          required={required}
          InputProps={{
            ...params.InputProps,
            startAdornment: (
              <Box sx={{ mr: 1, display: 'flex', alignItems: 'center' }}>
                <Search color="action" fontSize="small" />
              </Box>
            )
          }}
        />
      )}
      renderOption={(props, option) => (
        <li {...props}>
          <Box>
            <Typography variant="body2">
              {getOptionLabel(option)}
            </Typography>
            {(option.email || option.code || option.description) && (
              <Typography variant="caption" color="textSecondary">
                {option.email || option.code || option.description}
              </Typography>
            )}
          </Box>
        </li>
      )}
      PopperComponent={CustomPopper}
      clearOnBlur={false}
      selectOnFocus
      handleHomeEndKeys
      freeSolo={false}
    />
  );
};

export default SearchableDropdown;