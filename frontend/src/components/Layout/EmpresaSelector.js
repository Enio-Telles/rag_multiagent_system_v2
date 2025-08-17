import React, { useState } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  Typography,
  Chip,
  Avatar,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Business as BusinessIcon,
  KeyboardArrowDown as ArrowDownIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useEmpresa } from '../../contexts/EmpresaContext';

function EmpresaSelector() {
  const {
    empresas,
    empresaAtual,
    isLoading,
    error,
    selecionarEmpresa,
  } = useEmpresa();

  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleEmpresaSelect = async (empresa) => {
    handleClose();
    if (empresa.id !== empresaAtual?.id) {
      await selecionarEmpresa(empresa);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={16} color="inherit" />
        <Typography variant="body2" color="inherit">
          Carregando...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Chip
        label="Erro ao carregar empresas"
        color="error"
        size="small"
        variant="outlined"
      />
    );
  }

  if (!empresaAtual) {
    return (
      <Button
        variant="outlined"
        size="small"
        color="inherit"
        onClick={handleClick}
        sx={{
          borderColor: 'rgba(255, 255, 255, 0.3)',
          color: 'inherit',
          '&:hover': {
            borderColor: 'rgba(255, 255, 255, 0.5)',
            bgcolor: 'rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        Selecionar Empresa
      </Button>
    );
  }

  return (
    <>
      <Button
        onClick={handleClick}
        endIcon={<ArrowDownIcon />}
        sx={{
          color: 'inherit',
          textTransform: 'none',
          '&:hover': {
            bgcolor: 'rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar
            sx={{
              width: 24,
              height: 24,
              bgcolor: 'rgba(255, 255, 255, 0.2)',
              fontSize: '12px',
            }}
          >
            {empresaAtual.nome?.charAt(0)?.toUpperCase() || 'E'}
          </Avatar>
          <Box sx={{ textAlign: 'left', display: { xs: 'none', md: 'block' } }}>
            <Typography variant="body2" fontWeight="bold">
              {empresaAtual.nome}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              CNPJ: {empresaAtual.cnpj || 'N/A'}
            </Typography>
          </Box>
        </Box>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 320,
            maxHeight: 400,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Selecionar Empresa
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Escolha a empresa para trabalhar
          </Typography>
        </Box>
        
        <Divider />

        {!empresas || empresas.length === 0 ? (
          <Box sx={{ p: 2 }}>
            <Alert severity="info" size="small">
              Nenhuma empresa disponível
            </Alert>
          </Box>
        ) : (
          empresas.map((empresa) => (
            <MenuItem
              key={empresa.id}
              onClick={() => handleEmpresaSelect(empresa)}
              selected={empresa.id === empresaAtual?.id}
              sx={{
                py: 1.5,
                px: 2,
                '&.Mui-selected': {
                  bgcolor: 'primary.light',
                  '&:hover': {
                    bgcolor: 'primary.light',
                  },
                },
              }}
            >
              <ListItemIcon>
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    bgcolor: empresa.id === empresaAtual?.id ? 'primary.main' : 'grey.400',
                  }}
                >
                  {empresa.nome?.charAt(0)?.toUpperCase() || 'E'}
                </Avatar>
              </ListItemIcon>
              
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body1" fontWeight="medium">
                      {empresa.nome}
                    </Typography>
                    {empresa.id === empresaAtual?.id && (
                      <CheckIcon color="primary" fontSize="small" />
                    )}
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      CNPJ: {empresa.cnpj || 'N/A'}
                    </Typography>
                    {empresa.razao_social && empresa.razao_social !== empresa.nome && (
                      <Typography variant="caption" display="block" color="text.secondary">
                        {empresa.razao_social}
                      </Typography>
                    )}
                    <Box sx={{ mt: 0.5 }}>
                      <Chip
                        label={empresa.ativo ? 'Ativa' : 'Inativa'}
                        size="small"
                        color={empresa.ativo ? 'success' : 'default'}
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                }
              />
            </MenuItem>
          ))
        )}

        <Divider />
        
        <Box sx={{ p: 1 }}>
          <Button
            fullWidth
            variant="outlined"
            size="small"
            startIcon={<BusinessIcon />}
            onClick={() => {
              handleClose();
              // TODO: Implementar navegação para gestão de empresas
              alert('Funcionalidade em desenvolvimento');
            }}
          >
            Gerenciar Empresas
          </Button>
        </Box>
      </Menu>
    </>
  );
}

export default EmpresaSelector;
