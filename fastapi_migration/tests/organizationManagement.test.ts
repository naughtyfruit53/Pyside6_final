// fastapi_migration/frontend/tests/organizationManagement.test.tsx

import React from 'react';
import { render } from '@testing-library/react';
import OrganizationsPage from '../src/pages/admin/organizations/index';

describe('OrganizationsPage', () => {
  it('renders correctly', () => {
    const { getByText } = render(<OrganizationsPage />);
    expect(getByText('Organizations Management')).toBeInTheDocument();
  });
});