import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Alert, Snackbar } from '@mui/material';

interface ErrorMessage {
  id: string;
  message: string;
  type: 'error' | 'warning' | 'info' | 'success';
}

interface ErrorContextType {
  showError: (message: string, type?: 'error' | 'warning' | 'info' | 'success') => void;
  hideError: (id: string) => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

interface ErrorProviderProps {
  children: ReactNode;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({ children }) => {
  const [errors, setErrors] = useState<ErrorMessage[]>([]);

  const showError = (message: string, type: 'error' | 'warning' | 'info' | 'success' = 'error') => {
    const id = Date.now().toString();
    const newError: ErrorMessage = { id, message, type };
    
    setErrors(prev => [...prev, newError]);
    
    // Auto-hide after 6 seconds
    setTimeout(() => {
      hideError(id);
    }, 6000);
  };

  const hideError = (id: string) => {
    setErrors(prev => prev.filter(error => error.id !== id));
  };

  return (
    <ErrorContext.Provider value={{ showError, hideError }}>
      {children}
      
      {/* Render error snackbars */}
      {errors.map((error, index) => (
        <Snackbar
          key={error.id}
          open={true}
          autoHideDuration={6000}
          onClose={() => hideError(error.id)}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ mt: index * 7 }} // Stack multiple errors
        >
          <Alert 
            onClose={() => hideError(error.id)} 
            severity={error.type}
            sx={{ width: '100%' }}
          >
            {error.message}
          </Alert>
        </Snackbar>
      ))}
    </ErrorContext.Provider>
  );
};