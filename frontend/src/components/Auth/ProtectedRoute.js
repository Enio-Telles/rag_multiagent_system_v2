import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Mostrar loading enquanto verifica autenticação
  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        bgcolor="background.default"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Se não autenticado, redirecionar para login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Se autenticado, renderizar children
  return children;
}

export default ProtectedRoute;
