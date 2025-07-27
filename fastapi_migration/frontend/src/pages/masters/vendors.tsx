import React from 'react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

const VendorsRedirect: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main masters page with vendors tab
    router.replace('/masters?tab=vendors');
  }, [router]);

  return <div>Redirecting to vendors...</div>;
};

export default VendorsRedirect;