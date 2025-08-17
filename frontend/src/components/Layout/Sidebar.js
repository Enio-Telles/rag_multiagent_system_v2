import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  Divider,
  Typography,
  Chip,
  Badge,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Inventory as ProductsIcon,
  Assignment as ClassificationIcon,
  CheckCircle as ApprovalIcon,
  Assessment as AuditIcon,
  Settings as SettingsIcon,
  Group as UsersIcon,
  Business as CompaniesIcon,
  BarChart as ReportsIcon,
  Notifications as NotificationsIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useEmpresa } from '../../contexts/EmpresaContext';

const drawerWidth = 280;

const menuItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: DashboardIcon,
    path: '/dashboard',
    section: 'main',
  },
  {
    id: 'produtos',
    label: 'Produtos',
    icon: ProductsIcon,
    path: '/produtos',
    section: 'main',
    badge: 12, // Produtos pendentes
  },
  {
    id: 'classificacao',
    label: 'Classificação',
    icon: ClassificationIcon,
    path: '/classificacao',
    section: 'main',
    badge: 5, // Classificações pendentes
  },
  {
    id: 'aprovacao',
    label: 'Aprovação',
    icon: ApprovalIcon,
    path: '/aprovacao',
    section: 'main',
    badge: 3, // Aprovações pendentes
  },
  {
    id: 'auditoria',
    label: 'Auditoria',
    icon: AuditIcon,
    path: '/auditoria',
    section: 'main',
  },
  {
    id: 'relatorios',
    label: 'Relatórios',
    icon: ReportsIcon,
    path: '/relatorios',
    section: 'reports',
  },
  {
    id: 'usuarios',
    label: 'Usuários',
    icon: UsersIcon,
    path: '/usuarios',
    section: 'admin',
    permission: 'admin',
  },
  {
    id: 'empresas',
    label: 'Empresas',
    icon: CompaniesIcon,
    path: '/empresas',
    section: 'admin',
    permission: 'admin',
  },
  {
    id: 'configuracoes',
    label: 'Configurações',
    icon: SettingsIcon,
    path: '/configuracoes',
    section: 'admin',
  },
];

const sections = {
  main: 'Principal',
  reports: 'Relatórios',
  admin: 'Administração',
};

function Sidebar({ mobileOpen, onMobileClose }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { empresaAtual } = useEmpresa();

  const hasPermission = (permission) => {
    if (!permission) return true;
    return user?.permissions?.includes(permission) || user?.role === 'admin';
  };

  const filteredItems = menuItems.filter((item) => hasPermission(item.permission));

  const groupedItems = filteredItems.reduce((acc, item) => {
    if (!acc[item.section]) {
      acc[item.section] = [];
    }
    acc[item.section].push(item);
    return acc;
  }, {});

  const handleNavigation = (path) => {
    navigate(path);
    if (mobileOpen) {
      onMobileClose();
    }
  };

  const renderMenuItem = (item) => {
    const isActive = location.pathname === item.path;
    
    return (
      <ListItem key={item.id} disablePadding>
        <ListItemButton
          onClick={() => handleNavigation(item.path)}
          selected={isActive}
          sx={{
            minHeight: 48,
            px: 2.5,
            py: 1,
            '&.Mui-selected': {
              bgcolor: 'primary.light',
              borderRight: '3px solid',
              borderRightColor: 'primary.main',
              '&:hover': {
                bgcolor: 'primary.light',
              },
            },
            '&:hover': {
              bgcolor: 'action.hover',
            },
          }}
        >
          <ListItemIcon
            sx={{
              minWidth: 0,
              mr: 2,
              color: isActive ? 'primary.main' : 'inherit',
            }}
          >
            {item.badge ? (
              <Badge badgeContent={item.badge} color="error">
                <item.icon />
              </Badge>
            ) : (
              <item.icon />
            )}
          </ListItemIcon>
          
          <ListItemText
            primary={item.label}
            sx={{
              '& .MuiListItemText-primary': {
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'primary.main' : 'inherit',
              },
            }}
          />
          
          {item.badge && !isActive && (
            <Chip
              label={item.badge}
              size="small"
              color="error"
              sx={{ height: 20, fontSize: '0.75rem' }}
            />
          )}
        </ListItemButton>
      </ListItem>
    );
  };

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar />
      
      {/* Empresa Atual */}
      {empresaAtual && (
        <Box sx={{ px: 2, py: 1 }}>
          <Box
            sx={{
              p: 2,
              bgcolor: 'primary.light',
              borderRadius: 1,
              border: '1px solid',
              borderColor: 'primary.main',
            }}
          >
            <Typography variant="caption" color="primary.main" fontWeight="bold">
              EMPRESA ATUAL
            </Typography>
            <Typography variant="body2" fontWeight="medium" noWrap>
              {empresaAtual.nome}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap>
              CNPJ: {empresaAtual.cnpj || 'N/A'}
            </Typography>
          </Box>
        </Box>
      )}

      {/* Menu Navigation */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        {Object.entries(groupedItems).map(([sectionKey, items]) => (
          <Box key={sectionKey}>
            <Box sx={{ px: 2.5, py: 1, mt: sectionKey !== 'main' ? 2 : 1 }}>
              <Typography
                variant="overline"
                color="text.secondary"
                sx={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  letterSpacing: '0.5px',
                }}
              >
                {sections[sectionKey]}
              </Typography>
            </Box>
            
            <List disablePadding>
              {items.map(renderMenuItem)}
            </List>
            
            {sectionKey !== 'admin' && <Divider sx={{ my: 1 }} />}
          </Box>
        ))}
      </Box>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <List disablePadding>
          <ListItem disablePadding>
            <ListItemButton
              onClick={() => handleNavigation('/ajuda')}
              sx={{ minHeight: 40, px: 1 }}
            >
              <ListItemIcon sx={{ minWidth: 0, mr: 2 }}>
                <HelpIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary="Ajuda"
                sx={{
                  '& .MuiListItemText-primary': {
                    fontSize: '0.8rem',
                  },
                }}
              />
            </ListItemButton>
          </ListItem>
        </List>
        
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            display: 'block',
            textAlign: 'center',
            mt: 1,
            fontSize: '0.7rem',
          }}
        >
          RAG Multi-Agent v2.0
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box
      component="nav"
      sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
    >
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
      >
        {drawerContent}
      </Drawer>
      
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
        open
      >
        {drawerContent}
      </Drawer>
    </Box>
  );
}

export default Sidebar;
