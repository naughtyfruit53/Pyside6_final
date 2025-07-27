import React from 'react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

const SalesVoucherRedirect: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main vouchers page with sales tab
    router.replace('/vouchers?tab=sales');
  }, [router]);

  return <div>Redirecting to sales vouchers...</div>;
};

export default SalesVoucherRedirect;