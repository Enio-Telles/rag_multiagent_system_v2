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
  CircularProgress,
  Skeleton,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Inventory as ProductsIcon,
  Assignment as ClassificationIcon,
  CheckCircle as CheckCircleIcon,
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
import axios from 'axios';

// API Base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

function MetricCard({ title, value, variation, icon: Icon, color = 'primary', onClick }) {
  const isPositive = variation && variation > 0;
  const isNegative = variation && variation < 0;

  return (
    <Card 
      sx={{ 
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? { 
          boxShadow: 3,
          transform: 'translateY(-2px)',
          transition: 'all 0.2s ease-in-out'
        } : {}
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Avatar sx={{ bgcolor: `${color}.light`, color: `${color}.main` }}>
            <Icon />
          </Avatar>
          {variation && (
            <Chip
              icon={isPositive ? <TrendingUpIcon /> : <TrendingDownIcon />}
              label={`${variation > 0 ? '+' : ''}${variation}%`}
              color={isPositive ? 'success' : 'error'}
              size="small"
            />
          )}
        </Box>
        
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
      </CardContent>
    </Card>
  );
}

function Dashboard() {
  const navigate = useNavigate();
  const { empresaAtual } = useEmpresa();
  const { user } = useAuth();

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Função para buscar dados do dashboard
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`${API_BASE_URL}/dashboard/stats`);
      setDashboardData(response.data);
      setLastUpdate(new Date());
      
    } catch (err) {
      console.error('Erro ao buscar dados do dashboard:', err);
      setError('Erro ao carregar dados do dashboard. Usando dados de demonstração.');
      
      // Fallback para dados mock em caso de erro
      setDashboardData({
        resumo: {
          total_produtos: 1247,
          produtos_classificados: 1156,
          produtos_pendentes: 91,
          taxa_sucesso: 92.7,
          classificacoes_hoje: 156,
          golden_set_size: 45
        },
        agentes_performance: [
          { nome: 'NCM Agent', total_execucoes: 892, confianca_media: 96.2, tempo_medio_ms: 2100 },
          { nome: 'CEST Agent', total_execucoes: 567, confianca_media: 88.9, tempo_medio_ms: 4800 },
          { nome: 'Categoria Agent', total_execucoes: 1156, confianca_media: 97.8, tempo_medio_ms: 1300 }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  // Carregar dados ao montar o componente
  useEffect(() => {
    fetchDashboardData();
    
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(fetchDashboardData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Loading state
  if (loading && !dashboardData) {
    return (
      <Box>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Dashboard
        </Typography>
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((item) => (
            <Grid item xs={12} sm={6} md={3} key={item}>
              <Card>
                <CardContent>
                  <Skeleton variant="circular" width={40} height={40} />
                  <Skeleton variant="text" width="60%" sx={{ mt: 1 }} />
                  <Skeleton variant="text" width="40%" />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  const { resumo, agentes_performance } = dashboardData || {};

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Visão geral do sistema de classificação fiscal
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Última atualização: {lastUpdate.toLocaleTimeString()}
          </Typography>
          <IconButton onClick={fetchDashboardData} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Métricas Principais */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total de Produtos"
            value={resumo?.total_produtos || 0}
            variation={12.5}
            icon={ProductsIcon}
            color="primary"
            onClick={() => navigate('/produtos')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Produtos Classificados"
            value={resumo?.produtos_classificados || 0}
            variation={8.3}
            icon={CheckCircleIcon}
            color="success"
            onClick={() => navigate('/produtos?status=classificado')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Produtos Pendentes"
            value={resumo?.produtos_pendentes || 0}
            variation={-5.2}
            icon={WarningIcon}
            color="warning"
            onClick={() => navigate('/produtos?status=nao_classificado')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Taxa de Sucesso"
            value={`${resumo?.taxa_sucesso || 0}%`}
            variation={2.1}
            icon={TrendingUpIcon}
            color="info"
            onClick={() => navigate('/auditoria')}
          />
        </Grid>
      </Grid>

      {/* Seção de Ações Rápidas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Ações Rápidas
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<ClassificationIcon />}
                    onClick={() => navigate('/classificacao')}
                    sx={{ py: 2 }}
                  >
                    Nova Classificação
                  </Button>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<ApprovalIcon />}
                    onClick={() => navigate('/aprovacao')}
                    sx={{ py: 2 }}
                  >
                    Aprovar Classificações
                  </Button>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<ProductsIcon />}
                    onClick={() => navigate('/produtos')}
                    sx={{ py: 2 }}
                  >
                    Gerenciar Produtos
                  </Button>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<AuditIcon />}
                    onClick={() => navigate('/auditoria')}
                    sx={{ py: 2 }}
                  >
                    Ver Relatórios
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Status do Sistema
              </Typography>
              
              <List>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircle color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="API Online"
                    secondary="Todas as funcionalidades disponíveis"
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemIcon>
                    <AIIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`Base Padrão: ${resumo?.golden_set_size || 0} itens`}
                    secondary="Base de conhecimento atualizada"
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemIcon>
                    <TimelineIcon color="info" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`Classificações hoje: ${resumo?.classificacoes_hoje || 0}`}
                    secondary="Processamento ativo"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance dos Agentes */}
      {agentes_performance && agentes_performance.length > 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Performance dos Agentes de IA
                </Typography>
                
                <Grid container spacing={2}>
                  {agentes_performance.map((agente, index) => (
                    <Grid item xs={12} md={4} key={index}>
                      <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                          <Avatar sx={{ bgcolor: 'primary.light' }}>
                            <AIIcon color="primary" />
                          </Avatar>
                          <Box>
                            <Typography variant="subtitle1" fontWeight="bold">
                              {agente.nome}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {agente.total_execucoes} execuções
                            </Typography>
                          </Box>
                        </Box>
                        
                        <Box sx={{ mb: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Typography variant="body2">Confiança</Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {agente.confianca_media}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={agente.confianca_media}
                            sx={{ height: 6, borderRadius: 1 }}
                          />
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary">
                          Tempo médio: {Math.round(agente.tempo_medio_ms / 1000)}s
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}

export default Dashboard;
