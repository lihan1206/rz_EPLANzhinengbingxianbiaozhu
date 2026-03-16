import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';

import { getToken } from '../utils/storage';

export const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const token = getToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};
