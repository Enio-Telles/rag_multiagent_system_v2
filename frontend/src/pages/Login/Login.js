import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Container,
  InputAdornment,
  IconButton,
  Link,
  Alert,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Person as PersonIcon,
  Lock as LockIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../contexts/AuthContext';

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, isLoading } = useAuth();
  
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm();

  // Redirecionar se já autenticado
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Preencher com dados de demo
  useEffect(() => {
    setValue('username', 'admin');
    setValue('password', 'admin123');
  }, [setValue]);

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    setLoginError('');

    try {
      const result = await login({
        username: data.username,
        password: data.password,
      });

      if (result.success) {
        // Login bem-sucedido, redirecionamento será feito pelo useEffect
      } else {
        setLoginError(result.error || 'Erro ao fazer login');
      }
    } catch (error) {
      setLoginError('Erro inesperado. Tente novamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };

  // Mostrar loading se estiver verificando autenticação
  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
        }}
      >
        <Card sx={{ maxWidth: 400, width: '100%' }}>
          <CardContent sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom>
              Verificando autenticação...
            </Typography>
            <LinearProgress sx={{ mt: 2 }} />
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        backgroundImage: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
        },
      }}
    >
      <Container component="main" maxWidth="sm">
        <Card
          sx={{
            position: 'relative',
            backdropFilter: 'blur(20px)',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  mb: 2,
                }}
              >
                <BusinessIcon sx={{ fontSize: 40, color: 'white' }} />
              </Box>
              
              <Typography
                variant="h4"
                component="h1"
                gutterBottom
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  backgroundClip: 'text',
                  textFillColor: 'transparent',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                RAG Multi-Agent
              </Typography>
              
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Sistema Enterprise
              </Typography>
              
              <Typography variant="body2" color="text.secondary">
                Classificação Inteligente de Produtos
              </Typography>
            </Box>

            {/* Error Alert */}
            {loginError && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {loginError}
              </Alert>
            )}

            {/* Demo credentials info */}
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Credenciais de demonstração:</strong><br />
                Usuário: admin<br />
                Senha: admin123
              </Typography>
            </Alert>

            {/* Login Form */}
            <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
              <TextField
                margin="normal"
                required
                fullWidth
                label="Usuário"
                autoComplete="username"
                autoFocus
                error={!!errors.username}
                helperText={errors.username?.message}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <PersonIcon color="action" />
                    </InputAdornment>
                  ),
                }}
                {...register('username', {
                  required: 'Usuário é obrigatório',
                  minLength: {
                    value: 3,
                    message: 'Usuário deve ter pelo menos 3 caracteres',
                  },
                })}
              />

              <TextField
                margin="normal"
                required
                fullWidth
                label="Senha"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                error={!!errors.password}
                helperText={errors.password?.message}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleTogglePassword}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                {...register('password', {
                  required: 'Senha é obrigatória',
                  minLength: {
                    value: 6,
                    message: 'Senha deve ter pelo menos 6 caracteres',
                  },
                })}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={isSubmitting}
                sx={{
                  mt: 3,
                  mb: 2,
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                  },
                }}
              >
                {isSubmitting ? 'Entrando...' : 'Entrar'}
              </Button>

              <Divider sx={{ my: 2 }}>ou</Divider>

              <Box sx={{ textAlign: 'center' }}>
                <Link
                  component="button"
                  variant="body2"
                  onClick={(e) => {
                    e.preventDefault();
                    // TODO: Implementar recuperação de senha
                    alert('Funcionalidade em desenvolvimento');
                  }}
                >
                  Esqueceu sua senha?
                </Link>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Footer */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
            © 2025 RAG Multi-Agent Enterprise. Todos os direitos reservados.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default Login;
