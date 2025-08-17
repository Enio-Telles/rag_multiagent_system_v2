import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  IconButton,
  Chip,
  LinearProgress,
  Button,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
  Paper,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Inventory as ProductsIcon,
  Assignment as ClassificationIcon,
  CheckCircle as ApprovalIcon,
  Assessment as AuditIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  ArrowForward as ArrowForwardIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  AutoAwesome as AIIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useEmpresa } from '../../contexts/EmpresaContext';
import { useAuth } from '../../contexts/AuthContext';

// Mock data - em produção virá da API
const mockDashboardData = {
  metrics: {
    totalProdutos: 1247,
    totalProdutosVariacao: 12.5,
    produtosPendentes: 23,
    produtosPendentesVariacao: -5.2,
    classificacoesHoje: 156,
    classificacoesHojeVariacao: 8.3,
    precisaoIA: 94.7,
    precisaoIAVariacao: 2.1,
  },
  classificacoesPendentes: [
    {
      id: 1,
      produto: 'Smartphone Samsung Galaxy S23',
      categoria: 'Eletrônicos',
      confianca: 89,
      tempo: '2 horas atrás',
    },
    {
      id: 2,
      produto: 'Tênis Nike Air Max',
      categoria: 'Calçados',
      confianca: 76,
      tempo: '4 horas atrás',
    },
    {
      id: 3,
      produto: 'Livro JavaScript Avançado',
      categoria: 'Livros',
      confianca: 92,
      tempo: '6 horas atrás',
    },
  ],
  atividadesRecentes: [
    {
      id: 1,
      tipo: 'classificacao',
      descricao: 'Produto "iPhone 15 Pro" classificado como Eletrônicos',
      usuario: 'Ana Silva',
      tempo: '15 min atrás',
    },
    {
      id: 2,
      tipo: 'aprovacao',
      descricao: '12 classificações aprovadas em lote',
      usuario: 'Carlos Santos',
      tempo: '1 hora atrás',
    },
    {
      id: 3,
      tipo: 'auditoria',
      descricao: 'Relatório mensal de precisão gerado',
      usuario: 'Sistema',
      tempo: '2 horas atrás',
    },
  ],
};

function MetricCard({ title, value, variation, icon: Icon, color = 'primary' }) {
  const isPositive = variation > 0;
  const isNegative = variation < 0;

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Avatar sx={{ bgcolor: `${color}.light`, color: `${color}.main` }}>
            <Icon />
          </Avatar>
          <IconButton size="small" color="default">
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Box>
        
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {isPositive && <TrendingUpIcon color="success" fontSize="small" />}
          {isNegative && <TrendingDownIcon color="error" fontSize="small" />}
          
          <Typography
            variant="body2"
            color={isPositive ? 'success.main' : isNegative ? 'error.main' : 'text.secondary'}
            fontWeight="medium"
          >
            {variation > 0 ? '+' : ''}{variation}%
          </Typography>
          
          <Typography variant="body2" color="text.secondary">
            vs mês anterior
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

function Dashboard() {
  const navigate = useNavigate();
  const { empresaAtual } = useEmpresa();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(mockDashboardData);

  useEffect(() => {
    // Simular carregamento de dados
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const getActivityIcon = (tipo) => {
    switch (tipo) {
      case 'classificacao':
        return <ClassificationIcon color="primary" />;
      case 'aprovacao':
        return <ApprovalIcon color="success" />;
      case 'auditoria':
        return <AuditIcon color="info" />;
      default:
        return <TimelineIcon />;
    }
  };

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <LinearProgress />
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Carregando dados do dashboard...
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Dashboard
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography variant="body1" color="text.secondary">
            Bem-vindo de volta, <strong>{user?.nome || user?.username}</strong>!
          </Typography>
          
          {empresaAtual && (
            <Chip
              label={`${empresaAtual.nome}`}
              color="primary"
              variant="outlined"
              size="small"
            />
          )}
        </Box>

        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Novidade:</strong> Sistema de classificação automática com IA agora disponível! 
            <Button size="small" sx={{ ml: 1 }}>
              Saiba mais
            </Button>
          </Typography>
        </Alert>
      </Box>

      {/* Métricas Principais */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total de Produtos"
            value={data.metrics.totalProdutos}
            variation={data.metrics.totalProdutosVariacao}
            icon={ProductsIcon}
            color="primary"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Pendentes"
            value={data.metrics.produtosPendentes}
            variation={data.metrics.produtosPendentesVariacao}
            icon={WarningIcon}
            color="warning"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Classificações Hoje"
            value={data.metrics.classificacoesHoje}
            variation={data.metrics.classificacoesHojeVariacao}
            icon={SpeedIcon}
            color="success"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Precisão da IA"
            value={`${data.metrics.precisaoIA}%`}
            variation={data.metrics.precisaoIAVariacao}
            icon={AIIcon}
            color="info"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Classificações Pendentes */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6" fontWeight="bold">
                  Classificações Pendentes
                </Typography>
                <Button
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => navigate('/classificacao')}
                >
                  Ver todas
                </Button>
              </Box>

              <List>
                {data.classificacoesPendentes.map((item, index) => (
                  <Box key={item.id}>
                    <ListItem
                      sx={{
                        px: 0,
                        '&:hover': {
                          bgcolor: 'action.hover',
                          borderRadius: 1,
                        },
                      }}
                    >
                      <ListItemIcon>
                        <Avatar sx={{ bgcolor: 'primary.light', width: 40, height: 40 }}>
                          <ClassificationIcon color="primary" />
                        </Avatar>
                      </ListItemIcon>
                      
                      <ListItemText
                        primary={
                          <Typography variant="body1" fontWeight="medium">
                            {item.produto}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                              <Chip
                                label={item.categoria}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                              <Chip
                                label={`${item.confianca}% confiança`}
                                size="small"
                                color={item.confianca > 85 ? 'success' : 'warning'}
                              />
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              {item.tempo}
                            </Typography>
                          </Box>
                        }
                      />
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button size="small" variant="outlined" color="success">
                          Aprovar
                        </Button>
                        <Button size="small" variant="outlined">
                          Revisar
                        </Button>
                      </Box>
                    </ListItem>
                    
                    {index < data.classificacoesPendentes.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Atividades Recentes */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6" fontWeight="bold">
                  Atividades Recentes
                </Typography>
                <Button
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => navigate('/auditoria')}
                >
                  Ver todas
                </Button>
              </Box>

              <List>
                {data.atividadesRecentes.map((atividade, index) => (
                  <Box key={atividade.id}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        {getActivityIcon(atividade.tipo)}
                      </ListItemIcon>
                      
                      <ListItemText
                        primary={
                          <Typography variant="body2">
                            {atividade.descricao}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              por {atividade.usuario}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {atividade.tempo}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    
                    {index < data.atividadesRecentes.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Ações Rápidas
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<ProductsIcon />}
                    onClick={() => navigate('/produtos')}
                    sx={{ py: 1.5 }}
                  >
                    Produtos
                  </Button>
                </Grid>
                
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<ClassificationIcon />}
                    onClick={() => navigate('/classificacao')}
                    sx={{ py: 1.5 }}
                  >
                    Classificar
                  </Button>
                </Grid>
                
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<ApprovalIcon />}
                    onClick={() => navigate('/aprovacao')}
                    sx={{ py: 1.5 }}
                  >
                    Aprovar
                  </Button>
                </Grid>
                
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<AuditIcon />}
                    onClick={() => navigate('/auditoria')}
                    sx={{ py: 1.5 }}
                  >
                    Relatórios
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;
