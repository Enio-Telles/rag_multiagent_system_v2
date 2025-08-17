import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Alert,
  LinearProgress,
  Chip,
  Avatar,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Divider,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Sync as SyncIcon,
  AutoAwesome as AIIcon,
  Assessment as ReportIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Memory as ProcessorIcon,
  Storage as DatabaseIcon,
  CloudSync as CloudSyncIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useEmpresa } from '../../contexts/EmpresaContext';
import axios from 'axios';

// API Base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Steps do processo
const processSteps = [
  {
    id: 'sync',
    label: 'Sincronizar Produtos',
    description: 'Buscar novos produtos do banco de dados da empresa',
    icon: SyncIcon,
    color: 'primary',
    estimatedTime: '2-5 minutos',
    endpoint: '/processo/sincronizar'
  },
  {
    id: 'classify',
    label: 'Classificar Produtos',
    description: 'Executar classificação automática com IA',
    icon: AIIcon,
    color: 'secondary',
    estimatedTime: '5-15 minutos',
    endpoint: '/processo/classificar-lote'
  },
  {
    id: 'review',
    label: 'Revisar Resultados',
    description: 'Analisar e aprovar classificações geradas',
    icon: ReportIcon,
    color: 'success',
    estimatedTime: '10-30 minutos',
    navigateTo: '/aprovacao'
  }
];

function Processo() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { empresaAtual } = useEmpresa();

  // Estados principais
  const [activeStep, setActiveStep] = useState(0);
  const [stepStatus, setStepStatus] = useState({
    sync: 'pending', // pending, running, completed, error
    classify: 'pending',
    review: 'pending'
  });
  const [sessionIds, setSessionIds] = useState({});
  const [stepResults, setStepResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Estados dos parâmetros
  const [classificationParams, setClassificationParams] = useState({
    limite_produtos: null,
    apenas_pendentes: true
  });
  const [confirmDialog, setConfirmDialog] = useState({ open: false, step: null });

  // Função para executar um passo
  const executeStep = async (stepId) => {
    try {
      setLoading(true);
      setError(null);
      setStepStatus(prev => ({ ...prev, [stepId]: 'running' }));

      const step = processSteps.find(s => s.id === stepId);
      let response;

      if (stepId === 'sync') {
        response = await axios.post(`${API_BASE_URL}${step.endpoint}`);
      } else if (stepId === 'classify') {
        response = await axios.post(`${API_BASE_URL}${step.endpoint}`, null, {
          params: classificationParams
        });
      }

      if (response) {
        setSessionIds(prev => ({ ...prev, [stepId]: response.data.sessao_id }));
        
        // Monitorar progresso
        monitorProgress(stepId, response.data.sessao_id);
      }

    } catch (err) {
      console.error(`Erro no passo ${stepId}:`, err);
      setStepStatus(prev => ({ ...prev, [stepId]: 'error' }));
      setError(`Erro ao executar ${stepId}: ${err.message}`);
      setLoading(false);
    }
  };

  // Função para monitorar progresso
  const monitorProgress = async (stepId, sessionId) => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/processo/status/${sessionId}`);
        const status = response.data.status;

        if (status === 'completed' || status === 'success') {
          setStepStatus(prev => ({ ...prev, [stepId]: 'completed' }));
          setStepResults(prev => ({ 
            ...prev, 
            [stepId]: {
              message: response.data.mensagem || 'Processo concluído com sucesso',
              progress: 100,
              data: response.data
            }
          }));
          setLoading(false);
          
          // Avançar para próximo passo se não for o último
          if (stepId !== 'review') {
            const currentIndex = processSteps.findIndex(s => s.id === stepId);
            if (currentIndex < processSteps.length - 1) {
              setTimeout(() => setActiveStep(currentIndex + 1), 1000);
            }
          }
          
        } else if (status === 'error' || status === 'failed') {
          setStepStatus(prev => ({ ...prev, [stepId]: 'error' }));
          setError(response.data.mensagem || 'Erro no processamento');
          setLoading(false);
          
        } else {
          // Ainda processando, verificar novamente em 2 segundos
          setStepResults(prev => ({ 
            ...prev, 
            [stepId]: {
              message: response.data.mensagem || 'Processando...',
              progress: response.data.progresso || 0
            }
          }));
          setTimeout(checkStatus, 2000);
        }
        
      } catch (err) {
        console.error('Erro ao verificar status:', err);
        setStepStatus(prev => ({ ...prev, [stepId]: 'error' }));
        setError('Erro ao verificar status do processo');
        setLoading(false);
      }
    };

    // Iniciar monitoramento
    setTimeout(checkStatus, 1000);
  };

  // Função para resetar processo
  const resetProcess = () => {
    setActiveStep(0);
    setStepStatus({
      sync: 'pending',
      classify: 'pending',
      review: 'pending'
    });
    setSessionIds({});
    setStepResults({});
    setLoading(false);
    setError(null);
  };

  // Renderizar ícone de status
  const renderStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon color="success" />;
      case 'running':
        return <CircularProgress size={24} />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="disabled" />;
    }
  };

  // Renderizar cor do status
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'primary';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Execução do Processo de Classificação
        </Typography>
        
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Execute todas as etapas do sistema de classificação de forma simplificada
        </Typography>

        {/* Status Geral */}
        <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            icon={<ProcessorIcon />}
            label={`Empresa: ${empresaAtual?.nome || 'Sistema'}`}
            color="info"
            variant="outlined"
          />
          <Chip
            icon={<DatabaseIcon />}
            label="API Conectada"
            color="success"
            variant="outlined"
          />
          <Button variant="outlined" size="small" onClick={resetProcess}>
            Reiniciar Processo
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stepper Principal */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Fluxo de Execução
              </Typography>
              
              <Stepper activeStep={activeStep} orientation="vertical">
                {processSteps.map((step, index) => (
                  <Step key={step.id}>
                    <StepLabel
                      StepIconComponent={() => (
                        <Avatar sx={{ bgcolor: `${step.color}.light` }}>
                          {renderStatusIcon(stepStatus[step.id])}
                        </Avatar>
                      )}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {step.label}
                        </Typography>
                        <Chip
                          label={stepStatus[step.id]}
                          color={getStatusColor(stepStatus[step.id])}
                          size="small"
                        />
                      </Box>
                    </StepLabel>
                    
                    <StepContent>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {step.description}
                      </Typography>
                      
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Tempo estimado: {step.estimatedTime}
                      </Typography>

                      {/* Progresso do passo atual */}
                      {stepStatus[step.id] === 'running' && stepResults[step.id] && (
                        <Box sx={{ mt: 2 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={stepResults[step.id].progress || 0}
                            sx={{ mb: 1 }}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {stepResults[step.id].message}
                          </Typography>
                        </Box>
                      )}

                      {/* Resultado do passo */}
                      {stepStatus[step.id] === 'completed' && stepResults[step.id] && (
                        <Alert severity="success" sx={{ mt: 2 }}>
                          {stepResults[step.id].message}
                        </Alert>
                      )}

                      {/* Parâmetros para classificação */}
                      {step.id === 'classify' && activeStep === index && stepStatus[step.id] === 'pending' && (
                        <Box sx={{ mt: 2, mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Parâmetros de Classificação
                          </Typography>
                          
                          <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                              <TextField
                                label="Limite de Produtos"
                                type="number"
                                value={classificationParams.limite_produtos || ''}
                                onChange={(e) => setClassificationParams({
                                  ...classificationParams,
                                  limite_produtos: e.target.value ? parseInt(e.target.value) : null
                                })}
                                fullWidth
                                size="small"
                                helperText="Deixe vazio para processar todos"
                              />
                            </Grid>
                            
                            <Grid item xs={12} md={6}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={classificationParams.apenas_pendentes}
                                    onChange={(e) => setClassificationParams({
                                      ...classificationParams,
                                      apenas_pendentes: e.target.checked
                                    })}
                                  />
                                }
                                label="Apenas produtos pendentes"
                              />
                            </Grid>
                          </Grid>
                        </Box>
                      )}

                      {/* Botões de ação */}
                      <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                        {step.id === 'review' ? (
                          <Button
                            variant="contained"
                            startIcon={<ReportIcon />}
                            onClick={() => navigate(step.navigateTo)}
                            disabled={stepStatus[step.id] !== 'pending'}
                          >
                            Ir para Aprovação
                          </Button>
                        ) : (
                          <Button
                            variant="contained"
                            startIcon={<StartIcon />}
                            onClick={() => setConfirmDialog({ open: true, step })}
                            disabled={stepStatus[step.id] === 'running' || stepStatus[step.id] === 'completed'}
                          >
                            {stepStatus[step.id] === 'completed' ? 'Concluído' : 'Executar'}
                          </Button>
                        )}
                        
                        {index > 0 && (
                          <Button
                            variant="outlined"
                            onClick={() => setActiveStep(index - 1)}
                            disabled={loading}
                          >
                            Voltar
                          </Button>
                        )}
                      </Box>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </CardContent>
          </Card>
        </Grid>

        {/* Painel Lateral de Informações */}
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            {/* Status dos Agentes */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Status dos Agentes
                  </Typography>
                  
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <AIIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Agente NCM"
                        secondary="Pronto para classificação"
                      />
                      <Chip label="Online" color="success" size="small" />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        <AIIcon color="secondary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Agente CEST"
                        secondary="Pronto para classificação"
                      />
                      <Chip label="Online" color="success" size="small" />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        <AIIcon color="info" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Agente Categoria"
                        secondary="Pronto para classificação"
                      />
                      <Chip label="Online" color="success" size="small" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Estatísticas Rápidas */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Estatísticas
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Produtos Total</Typography>
                      <Typography variant="body2" fontWeight="bold">1,247</Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Pendentes</Typography>
                      <Typography variant="body2" fontWeight="bold" color="warning.main">91</Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Classificados</Typography>
                      <Typography variant="body2" fontWeight="bold" color="success.main">1,156</Typography>
                    </Box>
                    
                    <Divider />
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Taxa de Sucesso</Typography>
                      <Typography variant="body2" fontWeight="bold" color="primary.main">92.7%</Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Ações Rápidas */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Ações Rápidas
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Button
                      variant="outlined"
                      startIcon={<AnalyticsIcon />}
                      onClick={() => navigate('/dashboard')}
                      fullWidth
                    >
                      Ver Dashboard
                    </Button>
                    
                    <Button
                      variant="outlined"
                      startIcon={<TimelineIcon />}
                      onClick={() => navigate('/auditoria')}
                      fullWidth
                    >
                      Relatórios
                    </Button>
                    
                    <Button
                      variant="outlined"
                      startIcon={<SpeedIcon />}
                      onClick={() => navigate('/produtos')}
                      fullWidth
                    >
                      Gerenciar Produtos
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {/* Dialog de Confirmação */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, step: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Confirmar Execução
        </DialogTitle>
        <DialogContent>
          {confirmDialog.step && (
            <Box>
              <Typography variant="body1" gutterBottom>
                Deseja executar o passo: <strong>{confirmDialog.step.label}</strong>?
              </Typography>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {confirmDialog.step.description}
              </Typography>
              
              <Alert severity="info" sx={{ mt: 2 }}>
                Tempo estimado: {confirmDialog.step.estimatedTime}
              </Alert>

              {confirmDialog.step.id === 'classify' && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Parâmetros configurados:
                  </Typography>
                  <Typography variant="body2">
                    • Limite: {classificationParams.limite_produtos || 'Todos os produtos'}
                  </Typography>
                  <Typography variant="body2">
                    • Apenas pendentes: {classificationParams.apenas_pendentes ? 'Sim' : 'Não'}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, step: null })}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={() => {
              executeStep(confirmDialog.step.id);
              setConfirmDialog({ open: false, step: null });
            }}
            startIcon={<StartIcon />}
          >
            Executar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Processo;
