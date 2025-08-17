import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Tabs,
  Tab,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Checkbox,
  FormControlLabel,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Avatar,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  LinearProgress,
  Tooltip,
  Fab,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Comment as CommentIcon,
  History as HistoryIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  AutoAwesome as AIIcon,
  Category as CategoryIcon,
  Code as CodeIcon,
  Assignment as TaskIcon,
  DoneAll as ApproveAllIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useEmpresa } from '../../contexts/EmpresaContext';

// Mock data para demonstração
const mockAprovacoes = [
  {
    id: 1,
    produto: {
      id: 101,
      nome: 'Smartphone Samsung Galaxy S23 Ultra 256GB',
      descricao: 'Smartphone premium com câmera de 200MP',
      codigo_barras: '7893123456789',
    },
    classificacao: {
      categoria_atual: 'Eletrônicos',
      categoria_sugerida: 'Telefones Celulares',
      ncm_atual: '85171200',
      ncm_sugerido: '85171200',
      cest_atual: '2140300',
      cest_sugerido: '2140300',
      confianca_ia: 96.5,
    },
    workflow: {
      status: 'pendente_aprovacao',
      etapa_atual: 'revisor_tecnico',
      data_submissao: '2024-03-15T10:30:00',
      prazo: '2024-03-18T17:00:00',
      prioridade: 'alta',
    },
    historico: [
      {
        data: '2024-03-15T10:30:00',
        acao: 'Classificação automática realizada',
        usuario: 'Sistema IA',
        detalhes: 'Confiança: 96.5%',
      },
      {
        data: '2024-03-15T14:15:00',
        acao: 'Enviado para aprovação',
        usuario: 'Ana Silva',
        detalhes: 'Aguardando revisor técnico',
      },
    ],
    comentarios: [
      {
        id: 1,
        usuario: 'Carlos Santos',
        data: '2024-03-15T15:30:00',
        texto: 'Classificação parece correta, mas verificar se NCM está atualizado.',
        tipo: 'comentario',
      },
    ],
  },
  {
    id: 2,
    produto: {
      id: 102,
      nome: 'Tênis Nike Air Max 270 Masculino',
      descricao: 'Tênis esportivo com tecnologia Air Max',
      codigo_barras: '7891234567890',
    },
    classificacao: {
      categoria_atual: null,
      categoria_sugerida: 'Calçados Esportivos',
      ncm_atual: null,
      ncm_sugerido: '64041100',
      cest_atual: null,
      cest_sugerido: '2840100',
      confianca_ia: 78.3,
    },
    workflow: {
      status: 'em_revisao',
      etapa_atual: 'especialista_fiscal',
      data_submissao: '2024-03-14T09:15:00',
      prazo: '2024-03-17T17:00:00',
      prioridade: 'media',
    },
    historico: [
      {
        data: '2024-03-14T09:15:00',
        acao: 'Classificação automática realizada',
        usuario: 'Sistema IA',
        detalhes: 'Confiança: 78.3%',
      },
      {
        data: '2024-03-14T11:30:00',
        acao: 'Iniciada revisão técnica',
        usuario: 'Maria Oliveira',
        detalhes: 'Verificando categoria e NCM',
      },
    ],
    comentarios: [],
  },
];

const workflowSteps = [
  { id: 'classificacao_ia', label: 'Classificação IA', icon: AIIcon },
  { id: 'revisor_tecnico', label: 'Revisor Técnico', icon: PersonIcon },
  { id: 'especialista_fiscal', label: 'Especialista Fiscal', icon: TaskIcon },
  { id: 'aprovacao_final', label: 'Aprovação Final', icon: ApproveIcon },
];

const priorityColors = {
  alta: 'error',
  media: 'warning',
  baixa: 'info',
};

const statusColors = {
  pendente_aprovacao: 'warning',
  em_revisao: 'info',
  aprovado: 'success',
  rejeitado: 'error',
  em_correcao: 'warning',
};

function Aprovacao() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { empresaAtual } = useEmpresa();

  const [tabValue, setTabValue] = useState(0);
  const [aprovacoes, setAprovacoes] = useState(mockAprovacoes);
  const [selectedAprovacao, setSelectedAprovacao] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [batchMode, setBatchMode] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);
  const [newComment, setNewComment] = useState('');

  // Filtros
  const [filters, setFilters] = useState({
    status: 'todos',
    prioridade: 'todas',
    etapa: 'todas',
  });

  const tabs = [
    { label: 'Pendentes', count: aprovacoes.filter(a => a.workflow.status === 'pendente_aprovacao').length },
    { label: 'Em Revisão', count: aprovacoes.filter(a => a.workflow.status === 'em_revisao').length },
    { label: 'Aprovadas', count: aprovacoes.filter(a => a.workflow.status === 'aprovado').length },
    { label: 'Rejeitadas', count: aprovacoes.filter(a => a.workflow.status === 'rejeitado').length },
  ];

  const handleApprove = (aprovacaoId) => {
    setAprovacoes(prev => prev.map(a => 
      a.id === aprovacaoId 
        ? { 
            ...a, 
            workflow: { ...a.workflow, status: 'aprovado' },
            historico: [...a.historico, {
              data: new Date().toISOString(),
              acao: 'Aprovado',
              usuario: user?.nome || user?.username,
              detalhes: 'Classificação aprovada',
            }]
          }
        : a
    ));
  };

  const handleReject = (aprovacaoId, motivo = '') => {
    setAprovacoes(prev => prev.map(a => 
      a.id === aprovacaoId 
        ? { 
            ...a, 
            workflow: { ...a.workflow, status: 'rejeitado' },
            historico: [...a.historico, {
              data: new Date().toISOString(),
              acao: 'Rejeitado',
              usuario: user?.nome || user?.username,
              detalhes: motivo || 'Classificação rejeitada',
            }]
          }
        : a
    ));
  };

  const handleBatchApprove = () => {
    selectedItems.forEach(id => handleApprove(id));
    setSelectedItems([]);
    setBatchMode(false);
  };

  const handleAddComment = () => {
    if (selectedAprovacao && newComment.trim()) {
      const comment = {
        id: Date.now(),
        usuario: user?.nome || user?.username,
        data: new Date().toISOString(),
        texto: newComment,
        tipo: 'comentario',
      };

      setAprovacoes(prev => prev.map(a => 
        a.id === selectedAprovacao.id 
          ? { ...a, comentarios: [...a.comentarios, comment] }
          : a
      ));

      setNewComment('');
      setCommentDialogOpen(false);
    }
  };

  const getFilteredAprovacoes = () => {
    return aprovacoes.filter(aprovacao => {
      // Filtro por tab
      switch (tabValue) {
        case 0: return aprovacao.workflow.status === 'pendente_aprovacao';
        case 1: return aprovacao.workflow.status === 'em_revisao';
        case 2: return aprovacao.workflow.status === 'aprovado';
        case 3: return aprovacao.workflow.status === 'rejeitado';
        default: return true;
      }
    });
  };

  const getCurrentStepIndex = (etapaAtual) => {
    return workflowSteps.findIndex(step => step.id === etapaAtual);
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 24) {
      return `${diffInHours}h atrás`;
    } else {
      return `${Math.floor(diffInHours / 24)}d atrás`;
    }
  };

  const renderAprovacaoCard = (aprovacao) => (
    <Card key={aprovacao.id} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          {batchMode && (
            <Checkbox
              checked={selectedItems.includes(aprovacao.id)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedItems([...selectedItems, aprovacao.id]);
                } else {
                  setSelectedItems(selectedItems.filter(id => id !== aprovacao.id));
                }
              }}
            />
          )}

          <Avatar sx={{ bgcolor: 'primary.light' }}>
            <CategoryIcon color="primary" />
          </Avatar>

          <Box sx={{ flexGrow: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Typography variant="h6" fontWeight="bold">
                {aprovacao.produto.nome}
              </Typography>
              
              <Chip
                label={aprovacao.workflow.prioridade}
                size="small"
                color={priorityColors[aprovacao.workflow.prioridade]}
              />
              
              <Chip
                label={aprovacao.workflow.status.replace('_', ' ')}
                size="small"
                color={statusColors[aprovacao.workflow.status]}
              />
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              {aprovacao.produto.descricao}
            </Typography>

            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Categoria Sugerida:
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {aprovacao.classificacao.categoria_sugerida}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  NCM Sugerido:
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {aprovacao.classificacao.ncm_sugerido}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Confiança IA:
                </Typography>
                <Chip
                  label={`${aprovacao.classificacao.confianca_ia}%`}
                  size="small"
                  color={aprovacao.classificacao.confianca_ia >= 90 ? 'success' : 'warning'}
                />
              </Grid>
            </Grid>

            {/* Workflow Progress */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Progresso do Workflow:
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(getCurrentStepIndex(aprovacao.workflow.etapa_atual) + 1) / workflowSteps.length * 100}
                sx={{ height: 6, borderRadius: 1, mt: 1 }}
              />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Prazo: {formatTimeAgo(aprovacao.workflow.prazo)}
              </Typography>
              
              {aprovacao.comentarios.length > 0 && (
                <Chip
                  icon={<CommentIcon />}
                  label={aprovacao.comentarios.length}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Tooltip title="Ver detalhes">
              <IconButton
                onClick={() => {
                  setSelectedAprovacao(aprovacao);
                  setDetailsOpen(true);
                }}
              >
                <ViewIcon />
              </IconButton>
            </Tooltip>

            <Tooltip title="Adicionar comentário">
              <IconButton
                onClick={() => {
                  setSelectedAprovacao(aprovacao);
                  setCommentDialogOpen(true);
                }}
              >
                <CommentIcon />
              </IconButton>
            </Tooltip>

            {aprovacao.workflow.status === 'pendente_aprovacao' && (
              <>
                <Tooltip title="Aprovar">
                  <IconButton
                    color="success"
                    onClick={() => handleApprove(aprovacao.id)}
                  >
                    <ApproveIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Rejeitar">
                  <IconButton
                    color="error"
                    onClick={() => handleReject(aprovacao.id)}
                  >
                    <RejectIcon />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Aprovação de Classificações
        </Typography>
        
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Revise e aprove as classificações automáticas de produtos
        </Typography>

        {/* Estatísticas rápidas */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="warning.main" fontWeight="bold">
                  {aprovacoes.filter(a => a.workflow.status === 'pendente_aprovacao').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Pendentes
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="info.main" fontWeight="bold">
                  {aprovacoes.filter(a => a.workflow.status === 'em_revisao').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Em Revisão
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="success.main" fontWeight="bold">
                  {aprovacoes.filter(a => a.workflow.status === 'aprovado').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Aprovadas
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="primary.main" fontWeight="bold">
                  {Math.round(aprovacoes.reduce((acc, a) => acc + a.classificacao.confianca_ia, 0) / aprovacoes.length)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Confiança Média
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Ações e Filtros */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
            <Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={batchMode}
                    onChange={(e) => {
                      setBatchMode(e.target.checked);
                      if (!e.target.checked) {
                        setSelectedItems([]);
                      }
                    }}
                  />
                }
                label="Modo de aprovação em lote"
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 1 }}>
              {batchMode && selectedItems.length > 0 && (
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<ApproveAllIcon />}
                  onClick={handleBatchApprove}
                >
                  Aprovar {selectedItems.length} itens
                </Button>
              )}
              
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
              >
                Filtros
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

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
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {tab.label}
                  <Badge badgeContent={tab.count} color="primary" />
                </Box>
              }
            />
          ))}
        </Tabs>
      </Card>

      {/* Lista de Aprovações */}
      <Box>
        {getFilteredAprovacoes().map(renderAprovacaoCard)}
        
        {getFilteredAprovacoes().length === 0 && (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Nenhuma aprovação encontrada
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Não há itens na categoria selecionada.
            </Typography>
          </Paper>
        )}
      </Box>

      {/* Dialog de Detalhes */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Detalhes da Aprovação
        </DialogTitle>
        <DialogContent>
          {selectedAprovacao && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Typography variant="h6" gutterBottom>
                  {selectedAprovacao.produto.nome}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" paragraph>
                  {selectedAprovacao.produto.descricao}
                </Typography>

                {/* Comparação de classificação */}
                <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Comparação de Classificação
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Typography variant="caption" color="text.secondary">
                        Campo
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="caption" color="text.secondary">
                        Atual
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="caption" color="text.secondary">
                        Sugerido pela IA
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Divider />
                    </Grid>
                    
                    <Grid item xs={4}>
                      <Typography variant="body2">Categoria:</Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2">
                        {selectedAprovacao.classificacao.categoria_atual || 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2" fontWeight="bold" color="primary.main">
                        {selectedAprovacao.classificacao.categoria_sugerida}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={4}>
                      <Typography variant="body2">NCM:</Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2">
                        {selectedAprovacao.classificacao.ncm_atual || 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2" fontWeight="bold" color="primary.main">
                        {selectedAprovacao.classificacao.ncm_sugerido}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={4}>
                      <Typography variant="body2">CEST:</Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2">
                        {selectedAprovacao.classificacao.cest_atual || 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2" fontWeight="bold" color="primary.main">
                        {selectedAprovacao.classificacao.cest_sugerido}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>

                {/* Comentários */}
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Comentários ({selectedAprovacao.comentarios.length})
                </Typography>
                
                <List>
                  {selectedAprovacao.comentarios.map((comentario) => (
                    <ListItem key={comentario.id} divider>
                      <ListItemIcon>
                        <Avatar sx={{ width: 32, height: 32 }}>
                          {comentario.usuario.charAt(0)}
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={comentario.texto}
                        secondary={`${comentario.usuario} • ${formatTimeAgo(comentario.data)}`}
                      />
                    </ListItem>
                  ))}
                  
                  {selectedAprovacao.comentarios.length === 0 && (
                    <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                      Nenhum comentário ainda.
                    </Typography>
                  )}
                </List>
              </Grid>

              <Grid item xs={12} md={4}>
                {/* Workflow */}
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Workflow
                </Typography>
                
                <Stepper orientation="vertical" activeStep={getCurrentStepIndex(selectedAprovacao.workflow.etapa_atual)}>
                  {workflowSteps.map((step, index) => (
                    <Step key={step.id}>
                      <StepLabel
                        icon={<step.icon />}
                        optional={index === getCurrentStepIndex(selectedAprovacao.workflow.etapa_atual) && (
                          <Typography variant="caption">Em andamento</Typography>
                        )}
                      >
                        {step.label}
                      </StepLabel>
                    </Step>
                  ))}
                </Stepper>

                {/* Histórico */}
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom sx={{ mt: 3 }}>
                  Histórico
                </Typography>
                
                <Timeline>
                  {selectedAprovacao.historico.map((item, index) => (
                    <TimelineItem key={index}>
                      <TimelineSeparator>
                        <TimelineDot color="primary" />
                        {index < selectedAprovacao.historico.length - 1 && <TimelineConnector />}
                      </TimelineSeparator>
                      <TimelineContent>
                        <Typography variant="body2" fontWeight="medium">
                          {item.acao}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {item.usuario} • {formatTimeAgo(item.data)}
                        </Typography>
                        {item.detalhes && (
                          <Typography variant="caption" display="block" color="text.secondary">
                            {item.detalhes}
                          </Typography>
                        )}
                      </TimelineContent>
                    </TimelineItem>
                  ))}
                </Timeline>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>
            Fechar
          </Button>
          {selectedAprovacao?.workflow.status === 'pendente_aprovacao' && (
            <>
              <Button
                color="error"
                onClick={() => {
                  handleReject(selectedAprovacao.id);
                  setDetailsOpen(false);
                }}
              >
                Rejeitar
              </Button>
              <Button
                variant="contained"
                color="success"
                onClick={() => {
                  handleApprove(selectedAprovacao.id);
                  setDetailsOpen(false);
                }}
              >
                Aprovar
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Dialog de Comentário */}
      <Dialog
        open={commentDialogOpen}
        onClose={() => setCommentDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Adicionar Comentário</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            placeholder="Digite seu comentário..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentDialogOpen(false)}>
            Cancelar
          </Button>
          <Button variant="contained" onClick={handleAddComment}>
            Adicionar
          </Button>
        </DialogActions>
      </Dialog>

      {/* FAB para aprovação rápida */}
      <Fab
        color="success"
        aria-label="aprovar pendentes"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
        }}
        onClick={() => setTabValue(0)}
      >
        <Badge badgeContent={aprovacoes.filter(a => a.workflow.status === 'pendente_aprovacao').length} color="error">
          <ApproveIcon />
        </Badge>
      </Fab>
    </Box>
  );
}

export default Aprovacao;
