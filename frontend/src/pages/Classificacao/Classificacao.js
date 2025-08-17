import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Avatar,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  AutoAwesome as AIIcon,
  Psychology as BrainIcon,
  Speed as SpeedIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Category as CategoryIcon,
  Code as CodeIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useEmpresa } from '../../contexts/EmpresaContext';

// Mock data para demonstração
const mockClassificationJob = {
  id: 'job_001',
  status: 'em_andamento',
  total_produtos: 25,
  processados: 15,
  sucesso: 12,
  pendentes: 3,
  erros: 0,
  tempo_estimado: 180, // segundos
  tempo_decorrido: 120,
  produtos_processados: [
    {
      id: 1,
      nome: 'Smartphone Samsung Galaxy S23',
      status: 'sucesso',
      confianca: 96.5,
      categoria_sugerida: 'Eletrônicos',
      ncm_sugerido: '85171200',
      cest_sugerido: '2140300',
      tempo_processamento: 8.5,
    },
    {
      id: 2,
      nome: 'Tênis Nike Air Max',
      status: 'pendente',
      confianca: 75.2,
      categoria_sugerida: 'Calçados',
      ncm_sugerido: '64041100',
      cest_sugerido: '2840100',
      tempo_processamento: 12.3,
    },
  ],
};

const agentesIA = [
  {
    id: 'ncm_agent',
    nome: 'Agente NCM',
    descricao: 'Especialista em classificação fiscal NCM',
    status: 'ativo',
    precisao: 94.5,
    icon: CodeIcon,
  },
  {
    id: 'cest_agent',
    nome: 'Agente CEST',
    descricao: 'Especialista em ICMS-ST e CEST',
    status: 'ativo',
    precisao: 88.2,
    icon: CategoryIcon,
  },
  {
    id: 'categoria_agent',
    nome: 'Agente Categoria',
    descricao: 'Especialista em categorização de produtos',
    status: 'ativo',
    precisao: 97.8,
    icon: BrainIcon,
  },
];

function Classificacao() {
  const navigate = useNavigate();
  const location = useLocation();
  const { empresaAtual } = useEmpresa();

  const [activeStep, setActiveStep] = useState(0);
  const [classificacaoJob, setClassificacaoJob] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [agentesStatus, setAgentesStatus] = useState(agentesIA);

  // Parâmetros de configuração
  const [config, setConfig] = useState({
    modo: 'automatico',
    confianca_minima: 80,
    revisar_baixa_confianca: true,
    incluir_sugestoes: true,
    agentes_ativos: ['ncm_agent', 'cest_agent', 'categoria_agent'],
  });

  useEffect(() => {
    // Verificar se veio de um produto específico
    const params = new URLSearchParams(location.search);
    const produtoId = params.get('produto');
    if (produtoId) {
      // Carregar produto específico para classificação
      console.log('Classificar produto:', produtoId);
    }
  }, [location]);

  const steps = [
    'Configuração',
    'Seleção de Produtos',
    'Execução da IA',
    'Revisão e Aprovação',
  ];

  const handleStartClassification = () => {
    setIsRunning(true);
    setClassificacaoJob(mockClassificationJob);
    setActiveStep(2);

    // Simular progresso
    const interval = setInterval(() => {
      setClassificacaoJob(prev => {
        if (prev && prev.processados < prev.total_produtos) {
          return {
            ...prev,
            processados: prev.processados + 1,
            tempo_decorrido: prev.tempo_decorrido + 10,
          };
        } else {
          setIsRunning(false);
          setActiveStep(3);
          clearInterval(interval);
          return prev;
        }
      });
    }, 2000);

    return () => clearInterval(interval);
  };

  const handlePauseClassification = () => {
    setIsRunning(false);
  };

  const handleStopClassification = () => {
    setIsRunning(false);
    setClassificacaoJob(null);
    setActiveStep(0);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'sucesso':
        return 'success';
      case 'pendente':
        return 'warning';
      case 'erro':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'sucesso':
        return <SuccessIcon />;
      case 'pendente':
        return <WarningIcon />;
      case 'erro':
        return <ErrorIcon />;
      default:
        return <TimelineIcon />;
    }
  };

  const renderConfiguracao = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Configurações de Classificação
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Modo de Operação</InputLabel>
                  <Select
                    value={config.modo}
                    onChange={(e) => setConfig({ ...config, modo: e.target.value })}
                  >
                    <MenuItem value="automatico">Automático</MenuItem>
                    <MenuItem value="semi_automatico">Semi-automático</MenuItem>
                    <MenuItem value="manual">Manual</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Confiança Mínima (%)"
                  type="number"
                  value={config.confianca_minima}
                  onChange={(e) => setConfig({ ...config, confianca_minima: e.target.value })}
                  inputProps={{ min: 0, max: 100 }}
                />
              </Grid>
            </Grid>

            <Typography variant="subtitle1" sx={{ mt: 3, mb: 2 }}>
              Agentes de IA Disponíveis
            </Typography>

            {agentesStatus.map((agente) => (
              <Card key={agente.id} variant="outlined" sx={{ mb: 2 }}>
                <CardContent sx={{ py: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.light' }}>
                      <agente.icon color="primary" />
                    </Avatar>
                    
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {agente.nome}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {agente.descricao}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ textAlign: 'right' }}>
                      <Chip
                        label={`${agente.precisao}%`}
                        color="success"
                        size="small"
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="caption" display="block">
                        Precisão
                      </Typography>
                    </Box>
                    
                    <Chip
                      label={agente.status}
                      color={agente.status === 'ativo' ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Resumo da Classificação
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Empresa: {empresaAtual?.nome}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Produtos pendentes: 23
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Agentes ativos: {config.agentes_ativos.length}
              </Typography>
            </Box>

            <Button
              fullWidth
              variant="contained"
              size="large"
              startIcon={<PlayIcon />}
              onClick={() => setActiveStep(1)}
              sx={{ mt: 2 }}
            >
              Iniciar Classificação
            </Button>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderSelecaoProdutos = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Produtos para Classificação
            </Typography>

            <Alert severity="info" sx={{ mb: 2 }}>
              Foram encontrados 23 produtos sem classificação ou com baixa confiança.
            </Alert>

            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <Button
                variant="contained"
                startIcon={<AIIcon />}
                onClick={handleStartClassification}
              >
                Classificar Todos
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => setActiveStep(0)}
              >
                Voltar
              </Button>
            </Box>

            <Typography variant="subtitle2" gutterBottom>
              Produtos Selecionados (23)
            </Typography>
            
            <Paper variant="outlined" sx={{ maxHeight: 300, overflow: 'auto', p: 1 }}>
              <List dense>
                {mockClassificationJob.produtos_processados.map((produto, index) => (
                  <ListItem key={produto.id}>
                    <ListItemIcon>
                      <CategoryIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={produto.nome}
                      secondary={`Confiança atual: ${produto.confianca}%`}
                    />
                  </ListItem>
                ))}
                <ListItem>
                  <ListItemText primary="... e mais 21 produtos" />
                </ListItem>
              </List>
            </Paper>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderExecucao = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">
                Classificação em Andamento
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                {isRunning ? (
                  <Button
                    startIcon={<PauseIcon />}
                    onClick={handlePauseClassification}
                    color="warning"
                  >
                    Pausar
                  </Button>
                ) : (
                  <Button
                    startIcon={<PlayIcon />}
                    onClick={() => setIsRunning(true)}
                    color="primary"
                  >
                    Continuar
                  </Button>
                )}
                
                <Button
                  startIcon={<StopIcon />}
                  onClick={handleStopClassification}
                  color="error"
                >
                  Parar
                </Button>
              </Box>
            </Box>

            {classificacaoJob && (
              <>
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">
                      Progresso: {classificacaoJob.processados}/{classificacaoJob.total_produtos}
                    </Typography>
                    <Typography variant="body2">
                      {Math.round((classificacaoJob.processados / classificacaoJob.total_produtos) * 100)}%
                    </Typography>
                  </Box>
                  
                  <LinearProgress
                    variant="determinate"
                    value={(classificacaoJob.processados / classificacaoJob.total_produtos) * 100}
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                </Box>

                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main" fontWeight="bold">
                        {classificacaoJob.sucesso}
                      </Typography>
                      <Typography variant="caption">Sucesso</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="warning.main" fontWeight="bold">
                        {classificacaoJob.pendentes}
                      </Typography>
                      <Typography variant="caption">Pendentes</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="error.main" fontWeight="bold">
                        {classificacaoJob.erros}
                      </Typography>
                      <Typography variant="caption">Erros</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary.main" fontWeight="bold">
                        {Math.round(classificacaoJob.tempo_decorrido / 60)}m
                      </Typography>
                      <Typography variant="caption">Tempo</Typography>
                    </Box>
                  </Grid>
                </Grid>

                <Typography variant="subtitle2" gutterBottom>
                  Produtos Processados Recentemente
                </Typography>
                
                <List>
                  {classificacaoJob.produtos_processados.map((produto) => (
                    <ListItem key={produto.id} divider>
                      <ListItemIcon>
                        {getStatusIcon(produto.status)}
                      </ListItemIcon>
                      
                      <ListItemText
                        primary={produto.nome}
                        secondary={
                          <Box>
                            <Typography variant="caption">
                              {produto.categoria_sugerida} • NCM: {produto.ncm_sugerido}
                            </Typography>
                            <Chip
                              label={`${produto.confianca}%`}
                              size="small"
                              color={produto.confianca >= 80 ? 'success' : 'warning'}
                              sx={{ ml: 1 }}
                            />
                          </Box>
                        }
                      />
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton size="small" onClick={() => setSelectedProduct(produto)}>
                          <ViewIcon fontSize="small" />
                        </IconButton>
                        <IconButton size="small" onClick={() => setEditDialogOpen(true)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </ListItem>
                  ))}
                </List>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Status dos Agentes
            </Typography>

            {agentesStatus.map((agente) => (
              <Box key={agente.id} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <agente.icon fontSize="small" />
                  <Typography variant="body2" fontWeight="medium">
                    {agente.nome}
                  </Typography>
                  {isRunning && (
                    <CircularProgress size={16} />
                  )}
                </Box>
                
                <LinearProgress
                  variant={isRunning ? 'indeterminate' : 'determinate'}
                  value={isRunning ? undefined : 100}
                  color="primary"
                  sx={{ height: 4, borderRadius: 1 }}
                />
              </Box>
            ))}
          </CardContent>
        </Card>

        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Métricas em Tempo Real
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SpeedIcon color="primary" />
              <Box>
                <Typography variant="body2" fontWeight="medium">
                  Velocidade de Processamento
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  2.3 produtos/minuto
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUpIcon color="success" />
              <Box>
                <Typography variant="body2" fontWeight="medium">
                  Taxa de Sucesso
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  94.5% (últimos 100 produtos)
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderRevisao = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Revisão e Aprovação
            </Typography>

            <Alert severity="success" sx={{ mb: 3 }}>
              Classificação concluída! {classificacaoJob?.sucesso} produtos classificados com sucesso, 
              {classificacaoJob?.pendentes} produtos precisam de revisão.
            </Alert>

            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <Button
                variant="contained"
                color="success"
                onClick={() => navigate('/aprovacao')}
              >
                Ir para Aprovação
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => navigate('/produtos')}
              >
                Ver Produtos
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => {
                  setActiveStep(0);
                  setClassificacaoJob(null);
                }}
              >
                Nova Classificação
              </Button>
            </Box>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Produtos Classificados com Sucesso ({classificacaoJob?.sucesso})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {classificacaoJob?.produtos_processados
                    .filter(p => p.status === 'sucesso')
                    .map((produto) => (
                      <ListItem key={produto.id} divider>
                        <ListItemIcon>
                          <SuccessIcon color="success" />
                        </ListItemIcon>
                        <ListItemText
                          primary={produto.nome}
                          secondary={`${produto.categoria_sugerida} • NCM: ${produto.ncm_sugerido} • Confiança: ${produto.confianca}%`}
                        />
                      </ListItem>
                    ))}
                </List>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Produtos Pendentes de Revisão ({classificacaoJob?.pendentes})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {classificacaoJob?.produtos_processados
                    .filter(p => p.status === 'pendente')
                    .map((produto) => (
                      <ListItem key={produto.id} divider>
                        <ListItemIcon>
                          <WarningIcon color="warning" />
                        </ListItemIcon>
                        <ListItemText
                          primary={produto.nome}
                          secondary={`${produto.categoria_sugerida} • NCM: ${produto.ncm_sugerido} • Confiança: ${produto.confianca}%`}
                        />
                        <Button size="small" variant="outlined">
                          Revisar
                        </Button>
                      </ListItem>
                    ))}
                </List>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Classificação Inteligente
        </Typography>
        
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Use IA para classificar produtos automaticamente com NCM, CEST e categorias
        </Typography>
      </Box>

      {/* Stepper */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stepper activeStep={activeStep} orientation="horizontal">
            {steps.map((label, index) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Conteúdo do Step */}
      <Box>
        {activeStep === 0 && renderConfiguracao()}
        {activeStep === 1 && renderSelecaoProdutos()}
        {activeStep === 2 && renderExecucao()}
        {activeStep === 3 && renderRevisao()}
      </Box>

      {/* Dialog de Edição */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Editar Classificação</DialogTitle>
        <DialogContent>
          {selectedProduct && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  {selectedProduct.nome}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Categoria"
                  value={selectedProduct.categoria_sugerida}
                />
              </Grid>
              
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="NCM"
                  value={selectedProduct.ncm_sugerido}
                />
              </Grid>
              
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="CEST"
                  value={selectedProduct.cest_sugerido}
                />
              </Grid>
              
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Confiança (%)"
                  value={selectedProduct.confianca}
                  disabled
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>
            Cancelar
          </Button>
          <Button variant="contained" startIcon={<SaveIcon />}>
            Salvar
          </Button>
        </DialogActions>
      </Dialog>

      {/* FAB para ações rápidas */}
      {!isRunning && activeStep !== 2 && (
        <Fab
          color="primary"
          aria-label="classificação rápida"
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
          }}
          onClick={() => setActiveStep(1)}
        >
          <AIIcon />
        </Fab>
      )}
    </Box>
  );
}

export default Classificacao;
