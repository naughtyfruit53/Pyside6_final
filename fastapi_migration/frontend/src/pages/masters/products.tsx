import React from 'react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

const ProductsRedirect: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main masters page with products tab
    router.replace('/masters?tab=products');
  }, [router]);

  return <div>Redirecting to products...</div>;
};

export default ProductsRedirect;