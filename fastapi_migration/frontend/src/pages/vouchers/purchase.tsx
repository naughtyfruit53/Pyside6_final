import React from 'react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

const PurchaseVoucherRedirect: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main vouchers page with purchase tab
    router.replace('/vouchers?tab=purchase');
  }, [router]);

  return <div>Redirecting to purchase vouchers...</div>;
};

export default PurchaseVoucherRedirect;