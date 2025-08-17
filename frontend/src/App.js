import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { EmpresaProvider } from './contexts/EmpresaContext';

// Components
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// Pages
import Login from './pages/Login/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import Produtos from './pages/Produtos/Produtos';
import Classificacao from './pages/Classificacao/Classificacao';
import Aprovacao from './pages/Aprovacao/Aprovacao';
import Auditoria from './pages/Auditoria/Auditoria';
import Configuracoes from './pages/Configuracoes/Configuracoes';
import PerfilUsuario from './pages/PerfilUsuario/PerfilUsuario';

// Tema customizado
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#667eea',
      light: '#a5b4fc',
      dark: '#4338ca',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#764ba2',
      light: '#c084fc',
      dark: '#581c87',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#1e293b',
      secondary: '#64748b',
    },
    success: {
      main: '#10b981',
      light: '#34d399',
      dark: '#059669',
    },
    error: {
      main: '#ef4444',
      light: '#f87171',
      dark: '#dc2626',
    },
    warning: {
      main: '#f59e0b',
      light: '#fbbf24',
      dark: '#d97706',
    },
    info: {
      main: '#3b82f6',
      light: '#60a5fa',
      dark: '#2563eb',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: 8,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          border: '1px solid #e2e8f0',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        },
      },
    },
  },
});

// Configuração do React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutos
    },
  },
});

function App() {
  // Remover loading screen quando app carrega
  React.useEffect(() => {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
      loadingElement.style.display = 'none';
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <EmpresaProvider>
            <Router>
              <div className="App">
                <Routes>
                  {/* Rota de Login */}
                  <Route path="/login" element={<Login />} />
                  
                  {/* Rotas Protegidas */}
                  <Route path="/" element={
                    <ProtectedRoute>
                      <Layout />
                    </ProtectedRoute>
                  }>
                    {/* Dashboard Principal */}
                    <Route index element={<Dashboard />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    
                    {/* Gestão de Produtos */}
                    <Route path="produtos" element={<Produtos />} />
                    
                    {/* Classificação */}
                    <Route path="classificacao" element={<Classificacao />} />
                    
                    {/* Aprovação */}
                    <Route path="aprovacao" element={<Aprovacao />} />
                    
                    {/* Auditoria */}
                    <Route path="auditoria" element={<Auditoria />} />
                    
                    {/* Configurações */}
                    <Route path="configuracoes" element={<Configuracoes />} />
                    
                    {/* Perfil do Usuário */}
                    <Route path="perfil" element={<PerfilUsuario />} />
                  </Route>
                  
                  {/* Redirect para dashboard por padrão */}
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
                
                {/* Notificações Toast */}
                <Toaster
                  position="top-right"
                  toastOptions={{
                    duration: 4000,
                    style: {
                      background: '#363636',
                      color: '#fff',
                    },
                    success: {
                      style: {
                        background: '#10b981',
                      },
                    },
                    error: {
                      style: {
                        background: '#ef4444',
                      },
                    },
                  }}
                />
              </div>
            </Router>
          </EmpresaProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
