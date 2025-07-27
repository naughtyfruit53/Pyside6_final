import React from 'react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

const CustomersRedirect: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main masters page with customers tab
    router.replace('/masters?tab=customers');
  }, [router]);

  return <div>Redirecting to customers...</div>;
};

export default CustomersRedirect;