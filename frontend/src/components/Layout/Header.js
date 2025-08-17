import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Divider,
  Badge,
  Tooltip,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Notifications as NotificationsIcon,
  ExitToApp as LogoutIcon,
  Settings as SettingsIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useEmpresa } from '../../contexts/EmpresaContext';
import EmpresaSelector from './EmpresaSelector';

function Header({ onMenuToggle, mobileOpen }) {
  const { user, logout } = useAuth();
  const { empresaAtual } = useEmpresa();
  const [anchorEl, setAnchorEl] = useState(null);
  const [notificationsAnchor, setNotificationsAnchor] = useState(null);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleNotifications = (event) => {
    setNotificationsAnchor(event.currentTarget);
  };

  const handleCloseNotifications = () => {
    setNotificationsAnchor(null);
  };

  const handleLogout = async () => {
    handleClose();
    await logout();
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          edge="start"
          onClick={onMenuToggle}
          sx={{ mr: 2, display: { md: 'none' } }}
        >
          <MenuIcon />
        </IconButton>

        {/* Logo e Título */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <BusinessIcon sx={{ mr: 1, fontSize: 28 }} />
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}
          >
            RAG Multi-Agent
          </Typography>
          
          <Typography
            variant="body2"
            sx={{
              ml: 2,
              opacity: 0.8,
              display: { xs: 'none', sm: 'block' },
            }}
          >
            Enterprise Edition
          </Typography>
        </Box>

        {/* Empresa Atual */}
        <Box sx={{ mr: 2, display: { xs: 'none', md: 'flex' }, alignItems: 'center' }}>
          <EmpresaSelector />
        </Box>

        {/* Notificações */}
        <Box sx={{ mr: 1 }}>
          <Tooltip title="Notificações">
            <IconButton
              color="inherit"
              onClick={handleNotifications}
            >
              <Badge badgeContent={3} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          
          <Menu
            anchorEl={notificationsAnchor}
            open={Boolean(notificationsAnchor)}
            onClose={handleCloseNotifications}
            PaperProps={{
              sx: { width: 350, maxHeight: 400 }
            }}
          >
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Notificações
              </Typography>
            </Box>
            <Divider />
            
            <MenuItem onClick={handleCloseNotifications}>
              <Box>
                <Typography variant="body2" fontWeight="bold">
                  Nova classificação pendente
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  5 produtos aguardando aprovação
                </Typography>
              </Box>
            </MenuItem>
            
            <MenuItem onClick={handleCloseNotifications}>
              <Box>
                <Typography variant="body2" fontWeight="bold">
                  Auditoria concluída
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Relatório mensal disponível
                </Typography>
              </Box>
            </MenuItem>
            
            <MenuItem onClick={handleCloseNotifications}>
              <Box>
                <Typography variant="body2" fontWeight="bold">
                  Sistema atualizado
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Novas funcionalidades disponíveis
                </Typography>
              </Box>
            </MenuItem>
            
            <Divider />
            <Box sx={{ p: 1, textAlign: 'center' }}>
              <Button size="small" color="primary">
                Ver todas
              </Button>
            </Box>
          </Menu>
        </Box>

        {/* Menu do Usuário */}
        <Box>
          <Tooltip title="Conta do usuário">
            <IconButton
              size="large"
              onClick={handleMenu}
              color="inherit"
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  fontSize: '14px',
                }}
              >
                {user?.nome?.charAt(0)?.toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || 'U'}
              </Avatar>
            </IconButton>
          </Tooltip>
          
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            PaperProps={{
              sx: { width: 250 }
            }}
          >
            {/* Informações do Usuário */}
            <Box sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                  {user?.nome?.charAt(0)?.toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || 'U'}
                </Avatar>
                <Box>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {user?.nome || user?.username || 'Usuário'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {user?.email || 'usuario@empresa.com'}
                  </Typography>
                </Box>
              </Box>
              
              {empresaAtual && (
                <Box sx={{ mt: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Empresa atual:
                  </Typography>
                  <Typography variant="body2" fontWeight="500">
                    {empresaAtual.nome}
                  </Typography>
                </Box>
              )}
            </Box>
            
            <Divider />
            
            {/* Menu Items */}
            <MenuItem onClick={handleClose}>
              <PersonIcon sx={{ mr: 2 }} />
              Meu Perfil
            </MenuItem>
            
            <MenuItem onClick={handleClose}>
              <SettingsIcon sx={{ mr: 2 }} />
              Configurações
            </MenuItem>
            
            {/* Empresa Selector Mobile */}
            <Box sx={{ display: { md: 'none' } }}>
              <Divider />
              <Box sx={{ p: 2 }}>
                <EmpresaSelector />
              </Box>
            </Box>
            
            <Divider />
            
            <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
              <LogoutIcon sx={{ mr: 2 }} />
              Sair
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Header;
