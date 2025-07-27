// Mock jwt-decode functionality
export interface JwtPayload {
  sub?: string;
  email?: string;
  organization_id?: number;
  exp?: number;
  iat?: number;
}

export default function jwtDecode(token: string): JwtPayload {
  try {
    // Basic JWT decode simulation
    // In production, use a proper JWT library
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT token:', error);
    return {};
  }
}