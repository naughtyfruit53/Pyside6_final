import React from 'react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

const InventoryStockRedirect: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main inventory page
    router.replace('/inventory');
  }, [router]);

  return <div>Redirecting to inventory...</div>;
};

export default InventoryStockRedirect;