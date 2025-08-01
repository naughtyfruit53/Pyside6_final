// fastapi_migration/frontend/src/lib/jwtUtils.ts

import { jwtDecode } from 'jwt-decode';

export const decodeToken = (token: string): any => {
  try {
    return jwtDecode(token);
  } catch (error) {
    console.error('Failed to decode token', error);
    return null;
  }
};