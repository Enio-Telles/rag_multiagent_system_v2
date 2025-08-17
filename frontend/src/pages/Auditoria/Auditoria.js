import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Badge,
  CircularProgress,
} from '@mui/material';
import {
  Assessment as ReportIcon,
  Download as DownloadIcon,
  DateRange as DateIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Timeline as TimelineIcon,
  PieChart as ChartIcon,
  BarChart as BarChartIcon,
  ShowChart as LineChartIcon,
  FilterList as FilterIcon,
  Visibility as ViewIcon,
  Print as PrintIcon,
  Share as ShareIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  AutoAwesome as AIIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Category as CategoryIcon,
  Code as CodeIcon,
  Schedule as ScheduleIcon,
  Speed as SpeedIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { LocalizationProvider, DatePicker as MuiDatePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ptBR } from 'date-fns/locale';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useEmpresa } from '../../contexts/EmpresaContext';

// Mock data para demonstração
const mockAuditoriaData = {
  periodo: {
    inicio: '2024-03-01',
    fim: '2024-03-31',
  },
  metricas: {
    total_produtos: 1247,
    produtos_classificados: 1156,
    produtos_pendentes: 91,
    taxa_sucesso: 92.7,
    tempo_medio_classificacao: 3.2, // minutos
    economia_tempo: 87.5, // horas
    precisao_ia: 94.8,
    intervencoes_manuais: 156,
  },
  classificacoes_por_dia: [
    { data: '2024-03-01', total: 45, sucesso: 42, erro: 3 },
    { data: '2024-03-02', total: 52, sucesso: 48, erro: 4 },
    { data: '2024-03-03', total: 38, sucesso: 36, erro: 2 },
    // ... mais dados
  ],
  agentes_performance: [
    {
      id: 'ncm_agent',
      nome: 'Agente NCM',
      total_classificacoes: 892,
      taxa_sucesso: 96.2,
      tempo_medio: 2.1,
      economia_tempo: 34.5,
    },
    {
      id: 'cest_agent',
      nome: 'Agente CEST',
      total_classificacoes: 567,
      taxa_sucesso: 88.9,
      tempo_medio: 4.8,
      economia_tempo: 28.3,
    },
    {
      id: 'categoria_agent',
      nome: 'Agente Categoria',
      total_classificacoes: 1156,
      taxa_sucesso: 97.8,
      tempo_medio: 1.3,
      economia_tempo: 45.2,
    },
  ],
  top_categorias: [
    { categoria: 'Eletrônicos', total: 234, taxa_sucesso: 95.2 },
    { categoria: 'Calçados', total: 189, taxa_sucesso: 89.4 },
    { categoria: 'Roupas', total: 167, taxa_sucesso: 92.1 },
    { categoria: 'Livros', total: 145, taxa_sucesso: 98.6 },
    { categoria: 'Casa e Jardim', total: 123, taxa_sucesso: 87.8 },
  ],
  usuarios_atividade: [
    {
      usuario: 'Ana Silva',
      aprovacoes: 45,
      rejeicoes: 8,
      comentarios: 23,
      tempo_medio_analise: 4.2,
    },
    {
      usuario: 'Carlos Santos',
      aprovacoes: 67,
      rejeicoes: 12,
      comentarios: 34,
      tempo_medio_analise: 3.8,
    },
    {
      usuario: 'Maria Oliveira',
      aprovacoes: 52,
      rejeicoes: 6,
      comentarios: 19,
      tempo_medio_analise: 5.1,
    },
  ],
  alertas: [
    {
      id: 1,
      tipo: 'warning',
      titulo: 'Taxa de sucesso baixa em Eletrônicos',
      descricao: 'Categoria "Smartphones" teve apenas 78% de sucesso nos últimos 7 dias',
      data: '2024-03-15',
      prioridade: 'alta',
    },
    {
      id: 2,
      tipo: 'info',
      titulo: 'Novo padrão detectado',
      descricao: 'IA identificou novo padrão em produtos de beleza',
      data: '2024-03-14',
      prioridade: 'media',
    },
    {
      id: 3,
      tipo: 'error',
      titulo: 'Falha no agente CEST',
      descricao: 'Agente CEST teve 15 falhas consecutivas',
      data: '2024-03-13',
      prioridade: 'critica',
    },
  ],
};

const tiposRelatorio = [
  { id: 'geral', label: 'Relatório Geral', descricao: 'Visão geral completa do sistema' },
  { id: 'performance', label: 'Performance dos Agentes', descricao: 'Análise detalhada da performance da IA' },
  { id: 'usuarios', label: 'Atividade dos Usuários', descricao: 'Relatório de atividades dos usuários' },
  { id: 'categorias', label: 'Análise por Categorias', descricao: 'Performance por categoria de produto' },
  { id: 'compliance', label: 'Compliance Fiscal', descricao: 'Conformidade com regulamentações' },
];

function Auditoria() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { empresaAtual } = useEmpresa();

  const [tabValue, setTabValue] = useState(0);
  const [data, setData] = useState(mockAuditoriaData);
  const [periodo, setPeriodo] = useState({
    inicio: new Date('2024-03-01'),
    fim: new Date('2024-03-31'),
  });
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [selectedReportType, setSelectedReportType] = useState('geral');
  const [loading, setLoading] = useState(false);

  const tabs = [
    { label: 'Dashboard', icon: ReportIcon },
    { label: 'Performance', icon: TrendingUpIcon },
    { label: 'Atividades', icon: PersonIcon },
    { label: 'Alertas', icon: WarningIcon },
  ];

  const handleGenerateReport = () => {
    setLoading(true);
    // Simular geração de relatório
    setTimeout(() => {
      setLoading(false);
      setReportDialogOpen(false);
      // Simular download
      const link = document.createElement('a');
      link.href = '#';
      link.download = `relatorio_${selectedReportType}_${new Date().toISOString().split('T')[0]}.pdf`;
      link.click();
    }, 2000);
  };

  const getMetricIcon = (value, threshold, inverse = false) => {
    const isGood = inverse ? value < threshold : value > threshold;
    return isGood ? (
      <TrendingUpIcon color="success" />
    ) : (
      <TrendingDownIcon color="error" />
    );
  };

  const getMetricColor = (value, threshold, inverse = false) => {
    const isGood = inverse ? value < threshold : value > threshold;
    return isGood ? 'success' : 'error';
  };

  const renderDashboard = () => (
    <Grid container spacing={3}>
      {/* Métricas Principais */}
      <Grid item xs={12}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Métricas do Período
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Avatar sx={{ bgcolor: 'primary.light', mx: 'auto', mb: 1 }}>
                  <CategoryIcon color="primary" />
                </Avatar>
                <Typography variant="h4" fontWeight="bold">
                  {data.metricas.total_produtos.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total de Produtos
                </Typography>
                <Chip
                  label="+12.5%"
                  size="small"
                  color="success"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Avatar sx={{ bgcolor: 'success.light', mx: 'auto', mb: 1 }}>
                  <SuccessIcon color="success" />
                </Avatar>
                <Typography variant="h4" fontWeight="bold">
                  {data.metricas.taxa_sucesso}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Taxa de Sucesso
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 1 }}>
                  {getMetricIcon(data.metricas.taxa_sucesso, 90)}
                  <Typography variant="caption" color={getMetricColor(data.metricas.taxa_sucesso, 90)}>
                    +2.3%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Avatar sx={{ bgcolor: 'info.light', mx: 'auto', mb: 1 }}>
                  <AIIcon color="info" />
                </Avatar>
                <Typography variant="h4" fontWeight="bold">
                  {data.metricas.precisao_ia}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Precisão da IA
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 1 }}>
                  {getMetricIcon(data.metricas.precisao_ia, 90)}
                  <Typography variant="caption" color={getMetricColor(data.metricas.precisao_ia, 90)}>
                    +1.8%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Avatar sx={{ bgcolor: 'warning.light', mx: 'auto', mb: 1 }}>
                  <SpeedIcon color="warning" />
                </Avatar>
                <Typography variant="h4" fontWeight="bold">
                  {data.metricas.economia_tempo}h
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Economia de Tempo
                </Typography>
                <Chip
                  label="vs. processo manual"
                  size="small"
                  color="info"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Grid>

      {/* Gráfico de Atividade */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Atividade Diária de Classificação
            </Typography>
            
            {/* Placeholder para gráfico */}
            <Box
              sx={{
                height: 300,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: 'grey.50',
                borderRadius: 1,
                border: '1px dashed',
                borderColor: 'grey.300',
              }}
            >
              <Box sx={{ textAlign: 'center' }}>
                <LineChartIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                <Typography variant="body1" color="text.secondary">
                  Gráfico de Linha - Classificações por Dia
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Integração com biblioteca de gráficos necessária
                </Typography>
              </Box>
            </Box>

            <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
              <Chip icon={<SuccessIcon />} label="Sucessos" color="success" size="small" />
              <Chip icon={<ErrorIcon />} label="Erros" color="error" size="small" />
              <Chip icon={<WarningIcon />} label="Pendentes" color="warning" size="small" />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Top Categorias */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Top Categorias
            </Typography>
            
            <List>
              {data.top_categorias.map((categoria, index) => (
                <ListItem key={categoria.categoria} divider={index < data.top_categorias.length - 1}>
                  <ListItemIcon>
                    <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.light' }}>
                      <Typography variant="caption" fontWeight="bold">
                        {index + 1}
                      </Typography>
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={categoria.categoria}
                    secondary={
                      <Box>
                        <Typography variant="caption">
                          {categoria.total} produtos
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={categoria.taxa_sucesso}
                          sx={{ mt: 0.5, height: 4 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {categoria.taxa_sucesso}% sucesso
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>

      {/* Alertas Recentes */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Alertas e Notificações
            </Typography>
            
            <Grid container spacing={2}>
              {data.alertas.map((alerta) => (
                <Grid item xs={12} md={4} key={alerta.id}>
                  <Alert
                    severity={alerta.tipo}
                    action={
                      <IconButton size="small">
                        <ViewIcon fontSize="small" />
                      </IconButton>
                    }
                  >
                    <Typography variant="subtitle2" fontWeight="bold">
                      {alerta.titulo}
                    </Typography>
                    <Typography variant="body2">
                      {alerta.descricao}
                    </Typography>
                  </Alert>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderPerformance = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Performance dos Agentes de IA
        </Typography>
        
        <Grid container spacing={2}>
          {data.agentes_performance.map((agente) => (
            <Grid item xs={12} md={4} key={agente.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.light' }}>
                      <AIIcon color="primary" />
                    </Avatar>
                    <Box>
                      <Typography variant="h6" fontWeight="bold">
                        {agente.nome}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {agente.total_classificacoes} classificações
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Taxa de Sucesso</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {agente.taxa_sucesso}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={agente.taxa_sucesso}
                      color={agente.taxa_sucesso >= 90 ? 'success' : 'warning'}
                      sx={{ height: 6, borderRadius: 1 }}
                    />
                  </Box>

                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Tempo Médio
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {agente.tempo_medio}min
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Economia
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {agente.economia_tempo}h
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Grid>

      {/* Gráfico Comparativo */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Comparativo de Performance
            </Typography>
            
            <Box
              sx={{
                height: 400,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: 'grey.50',
                borderRadius: 1,
                border: '1px dashed',
                borderColor: 'grey.300',
              }}
            >
              <Box sx={{ textAlign: 'center' }}>
                <BarChartIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Gráfico de Barras Comparativo
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Performance dos agentes ao longo do tempo
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderAtividades = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Atividade dos Usuários
        </Typography>
        
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Usuário</TableCell>
                <TableCell align="center">Aprovações</TableCell>
                <TableCell align="center">Rejeições</TableCell>
                <TableCell align="center">Comentários</TableCell>
                <TableCell align="center">Tempo Médio</TableCell>
                <TableCell align="center">Taxa de Aprovação</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.usuarios_atividade.map((usuario) => (
                <TableRow key={usuario.usuario} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ width: 32, height: 32 }}>
                        {usuario.usuario.charAt(0)}
                      </Avatar>
                      <Typography variant="body2" fontWeight="medium">
                        {usuario.usuario}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={usuario.aprovacoes}
                      color="success"
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={usuario.rejeicoes}
                      color="error"
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={usuario.comentarios}
                      color="info"
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2">
                      {usuario.tempo_medio_analise}min
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" fontWeight="bold">
                        {Math.round((usuario.aprovacoes / (usuario.aprovacoes + usuario.rejeicoes)) * 100)}%
                      </Typography>
                      {Math.round((usuario.aprovacoes / (usuario.aprovacoes + usuario.rejeicoes)) * 100) >= 80 ? (
                        <TrendingUpIcon color="success" fontSize="small" />
                      ) : (
                        <TrendingDownIcon color="error" fontSize="small" />
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Grid>
    </Grid>
  );

  const renderAlertas = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Sistema de Alertas
        </Typography>
        
        {data.alertas.map((alerta) => (
          <Accordion key={alerta.id}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Avatar
                  sx={{
                    bgcolor: alerta.tipo === 'error' ? 'error.light' : 
                            alerta.tipo === 'warning' ? 'warning.light' : 'info.light',
                  }}
                >
                  {alerta.tipo === 'error' ? <ErrorIcon /> :
                   alerta.tipo === 'warning' ? <WarningIcon /> : <SuccessIcon />}
                </Avatar>
                
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {alerta.titulo}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {alerta.data} • Prioridade: {alerta.prioridade}
                  </Typography>
                </Box>
                
                <Chip
                  label={alerta.prioridade}
                  size="small"
                  color={
                    alerta.prioridade === 'critica' ? 'error' :
                    alerta.prioridade === 'alta' ? 'warning' : 'info'
                  }
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                {alerta.descricao}
              </Typography>
              
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button size="small" variant="outlined">
                  Investigar
                </Button>
                <Button size="small" variant="outlined">
                  Marcar como Resolvido
                </Button>
                <Button size="small" variant="outlined">
                  Criar Ticket
                </Button>
              </Box>
            </AccordionDetails>
          </Accordion>
        ))}
      </Grid>
    </Grid>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Auditoria e Relatórios
        </Typography>
        
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Análise detalhada da performance e atividades do sistema
        </Typography>

        {/* Controles de Período e Ações */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
          <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
            <MuiDatePicker
              label="Data Início"
              value={periodo.inicio}
              onChange={(newValue) => setPeriodo({ ...periodo, inicio: newValue })}
              renderInput={(params) => (
                <TextField {...params} size="small" sx={{ width: 150 }} />
              )}
            />
            <MuiDatePicker
              label="Data Fim"
              value={periodo.fim}
              onChange={(newValue) => setPeriodo({ ...periodo, fim: newValue })}
              renderInput={(params) => (
                <TextField {...params} size="small" sx={{ width: 150 }} />
              )}
            />
          </LocalizationProvider>

          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
          >
            Aplicar Filtro
          </Button>

          <Button
            variant="contained"
            startIcon={<ReportIcon />}
            onClick={() => setReportDialogOpen(true)}
          >
            Gerar Relatório
          </Button>

          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
          >
            Exportar Dados
          </Button>
        </Box>
      </Box>

      {/* Tabs */}
      <Card sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          variant="fullWidth"
        >
          {tabs.map((tab, index) => (
            <Tab
              key={index}
              icon={<tab.icon />}
              label={tab.label}
              iconPosition="start"
            />
          ))}
        </Tabs>
      </Card>

      {/* Conteúdo das Tabs */}
      <Box>
        {tabValue === 0 && renderDashboard()}
        {tabValue === 1 && renderPerformance()}
        {tabValue === 2 && renderAtividades()}
        {tabValue === 3 && renderAlertas()}
      </Box>

      {/* Dialog de Geração de Relatório */}
      <Dialog
        open={reportDialogOpen}
        onClose={() => setReportDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Gerar Relatório Personalizado
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControl fullWidth sx={{ mt: 1 }}>
                <InputLabel>Tipo de Relatório</InputLabel>
                <Select
                  value={selectedReportType}
                  onChange={(e) => setSelectedReportType(e.target.value)}
                >
                  {tiposRelatorio.map((tipo) => (
                    <MenuItem key={tipo.id} value={tipo.id}>
                      <Box>
                        <Typography variant="body1">{tipo.label}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {tipo.descricao}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Período do Relatório
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {periodo.inicio?.toLocaleDateString('pt-BR')} até {periodo.fim?.toLocaleDateString('pt-BR')}
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Empresa
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {empresaAtual?.nome || 'Todas as empresas'}
              </Typography>
            </Grid>
          </Grid>

          {loading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Gerando relatório...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReportDialogOpen(false)}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleGenerateReport}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <DownloadIcon />}
          >
            {loading ? 'Gerando...' : 'Gerar Relatório'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Auditoria;
