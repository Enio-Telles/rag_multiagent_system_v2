import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  InputAdornment,
  Alert,
  LinearProgress,
  Avatar,
  Tooltip,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Star as StarIcon,
  Inventory as InventoryIcon,
  Category as CategoryIcon,
  Code as CodeIcon,
  CheckCircle as SuccessIcon,
  School as KnowledgeIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useEmpresa } from '../../contexts/EmpresaContext';
import axios from 'axios';

// API Base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

function BasePadrao() {
  const { user } = useAuth();
  const { empresaAtual } = useEmpresa();

  // Estados principais
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Estados da interface
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);

  // Estados dos diálogos
  const [itemDialog, setItemDialog] = useState({ 
    open: false, 
    mode: 'create', // 'create', 'edit', 'view'
    item: null 
  });
  const [deleteDialog, setDeleteDialog] = useState({ open: false, item: null });

  // Estado do formulário
  const [formData, setFormData] = useState({
    produto_id: '',
    descricao_produto: '',
    descricao_completa: '',
    codigo_produto: '',
    gtin_validado: '',
    ncm_final: '',
    cest_final: '',
    fonte_validacao: 'HUMANA',
    justificativa_inclusao: '',
    qualidade_score: 1.0,
  });

  // Função para buscar itens da base padrão
  const fetchItems = async (search = '', pageNum = 0) => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: pageNum + 1,
        limit: rowsPerPage,
        ...(search && { search }),
      };

      const response = await axios.get(`${API_BASE_URL}/base-padrao`, { params });
      
      setItems(response.data.items);
      setTotalCount(response.data.pagination.total);
      
    } catch (err) {
      console.error('Erro ao buscar base padrão:', err);
      setError('Erro ao carregar base padrão. Verifique se a API está rodando.');
      
      // Fallback para dados mock
      setItems([
        {
          golden_set_id: '1',
          produto_id: 1001,
          descricao_produto: 'Smartphone Premium 256GB',
          ncm_final: '85171200',
          cest_final: '21.001.00',
          fonte_validacao: 'HUMANA',
          qualidade_score: 1.0,
          data_criacao: '2024-03-01T10:00:00'
        },
        {
          golden_set_id: '2',
          produto_id: 1002,
          descricao_produto: 'Tênis Esportivo Profissional',
          ncm_final: '64041100',
          cest_final: '04.006.00',
          fonte_validacao: 'ESPECIALISTA',
          qualidade_score: 0.95,
          data_criacao: '2024-03-01T11:00:00'
        }
      ]);
      setTotalCount(2);
    } finally {
      setLoading(false);
    }
  };

  // Effect para carregar dados
  useEffect(() => {
    fetchItems(searchTerm, page);
  }, [searchTerm, page, rowsPerPage]);

  // Função para busca
  const handleSearch = (event) => {
    if (event.key === 'Enter' || event.type === 'click') {
      setPage(0);
      fetchItems(searchTerm, 0);
    }
  };

  // Função para abrir dialog de criar/editar
  const handleOpenDialog = (mode, item = null) => {
    if (mode === 'create') {
      setFormData({
        produto_id: '',
        descricao_produto: '',
        descricao_completa: '',
        codigo_produto: '',
        gtin_validado: '',
        ncm_final: '',
        cest_final: '',
        fonte_validacao: 'HUMANA',
        justificativa_inclusao: '',
        qualidade_score: 1.0,
      });
    } else if (mode === 'edit' && item) {
      setFormData({
        produto_id: item.produto_id || '',
        descricao_produto: item.descricao_produto || '',
        descricao_completa: item.descricao_completa || '',
        codigo_produto: item.codigo_produto || '',
        gtin_validado: item.gtin_validado || '',
        ncm_final: item.ncm_final || '',
        cest_final: item.cest_final || '',
        fonte_validacao: item.fonte_validacao || 'HUMANA',
        justificativa_inclusao: item.justificativa_inclusao || '',
        qualidade_score: item.qualidade_score || 1.0,
      });
    }

    setItemDialog({ open: true, mode, item });
  };

  // Função para salvar item
  const handleSaveItem = async () => {
    try {
      const dataToSend = {
        ...formData,
        revisado_por: user?.name || 'Sistema',
      };

      if (itemDialog.mode === 'create') {
        await axios.post(`${API_BASE_URL}/base-padrao`, dataToSend);
        setSnackbar({
          open: true,
          message: 'Item adicionado à base padrão com sucesso',
          severity: 'success'
        });
      } else if (itemDialog.mode === 'edit') {
        await axios.put(`${API_BASE_URL}/base-padrao/${itemDialog.item.golden_set_id}`, dataToSend);
        setSnackbar({
          open: true,
          message: 'Item atualizado com sucesso',
          severity: 'success'
        });
      }

      setItemDialog({ open: false, mode: 'create', item: null });
      fetchItems(searchTerm, page);

    } catch (err) {
      console.error('Erro ao salvar item:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao salvar item',
        severity: 'error'
      });
    }
  };

  // Função para excluir item
  const handleDeleteItem = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/base-padrao/${deleteDialog.item.golden_set_id}`);
      
      setSnackbar({
        open: true,
        message: 'Item removido da base padrão',
        severity: 'success'
      });

      setDeleteDialog({ open: false, item: null });
      fetchItems(searchTerm, page);

    } catch (err) {
      console.error('Erro ao excluir item:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao excluir item',
        severity: 'error'
      });
    }
  };

  // Renderizar fonte de validação
  const renderFonteValidacao = (fonte) => {
    const colors = {
      'HUMANA': 'primary',
      'ESPECIALISTA': 'success',
      'SISTEMA': 'info',
      'IMPORTACAO': 'warning'
    };

    return (
      <Chip
        label={fonte}
        color={colors[fonte] || 'default'}
        size="small"
      />
    );
  };

  // Renderizar qualidade score
  const renderQualityScore = (score) => {
    const percentage = Math.round(score * 100);
    const color = percentage >= 90 ? 'success' : percentage >= 70 ? 'warning' : 'error';
    
    return (
      <Chip
        icon={<StarIcon />}
        label={`${percentage}%`}
        color={color}
        size="small"
        variant="outlined"
      />
    );
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Base de Produtos Padrão
        </Typography>
        
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Gerencie a base de conhecimento de produtos com classificações validadas
        </Typography>

        {/* Controles */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2 }}>
          <TextField
            placeholder="Buscar na base padrão..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={handleSearch}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            size="small"
            sx={{ width: 300 }}
          />
          
          <Button
            variant="outlined"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
          >
            Buscar
          </Button>

          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => fetchItems(searchTerm, page)}
            disabled={loading}
          >
            Atualizar
          </Button>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog('create')}
          >
            Adicionar Item
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Estatísticas */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'primary.light', mx: 'auto', mb: 1 }}>
                <KnowledgeIcon color="primary" />
              </Avatar>
              <Typography variant="h4" fontWeight="bold">
                {totalCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Itens na Base
              </Typography>
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
                {items.filter(item => item.qualidade_score >= 0.9).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Alta Qualidade
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'info.light', mx: 'auto', mb: 1 }}>
                <CategoryIcon color="info" />
              </Avatar>
              <Typography variant="h4" fontWeight="bold">
                {new Set(items.map(item => item.ncm_final?.substring(0, 4))).size}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Categorias NCM
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'warning.light', mx: 'auto', mb: 1 }}>
                <CodeIcon color="warning" />
              </Avatar>
              <Typography variant="h4" fontWeight="bold">
                {items.filter(item => item.cest_final).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Com CEST
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabela */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          {loading && <LinearProgress />}
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Produto</TableCell>
                  <TableCell>NCM</TableCell>
                  <TableCell>CEST</TableCell>
                  <TableCell>Fonte</TableCell>
                  <TableCell>Qualidade</TableCell>
                  <TableCell>Data</TableCell>
                  <TableCell>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.golden_set_id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Avatar sx={{ bgcolor: 'primary.light' }}>
                          <InventoryIcon />
                        </Avatar>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {item.descricao_produto}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ID: {item.produto_id}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {item.ncm_final}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      {item.cest_final || '-'}
                    </TableCell>
                    
                    <TableCell>
                      {renderFonteValidacao(item.fonte_validacao)}
                    </TableCell>
                    
                    <TableCell>
                      {renderQualityScore(item.qualidade_score)}
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(item.data_criacao).toLocaleDateString('pt-BR')}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="Ver detalhes">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenDialog('view', item)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Editar">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleOpenDialog('edit', item)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Excluir">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setDeleteDialog({ open: true, item })}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Paginação */}
          <TablePagination
            component="div"
            count={totalCount}
            page={page}
            onPageChange={(e, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[10, 25, 50, 100]}
            labelRowsPerPage="Linhas por página"
            labelDisplayedRows={({ from, to, count }) =>
              `${from}-${to} de ${count !== -1 ? count : `mais de ${to}`}`
            }
          />
        </CardContent>
      </Card>

      {/* Dialog de Criar/Editar Item */}
      <Dialog
        open={itemDialog.open}
        onClose={() => setItemDialog({ open: false, mode: 'create', item: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {itemDialog.mode === 'create' && 'Adicionar Item à Base Padrão'}
          {itemDialog.mode === 'edit' && 'Editar Item da Base Padrão'}
          {itemDialog.mode === 'view' && 'Detalhes do Item'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                label="ID do Produto"
                type="number"
                value={formData.produto_id}
                onChange={(e) => setFormData({ ...formData, produto_id: e.target.value })}
                fullWidth
                disabled={itemDialog.mode === 'view'}
                required
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="Código do Produto"
                value={formData.codigo_produto}
                onChange={(e) => setFormData({ ...formData, codigo_produto: e.target.value })}
                fullWidth
                disabled={itemDialog.mode === 'view'}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Descrição do Produto"
                value={formData.descricao_produto}
                onChange={(e) => setFormData({ ...formData, descricao_produto: e.target.value })}
                fullWidth
                disabled={itemDialog.mode === 'view'}
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Descrição Completa"
                value={formData.descricao_completa}
                onChange={(e) => setFormData({ ...formData, descricao_completa: e.target.value })}
                fullWidth
                multiline
                rows={2}
                disabled={itemDialog.mode === 'view'}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="GTIN Validado"
                value={formData.gtin_validado}
                onChange={(e) => setFormData({ ...formData, gtin_validado: e.target.value })}
                fullWidth
                disabled={itemDialog.mode === 'view'}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth disabled={itemDialog.mode === 'view'}>
                <InputLabel>Fonte de Validação</InputLabel>
                <Select
                  value={formData.fonte_validacao}
                  onChange={(e) => setFormData({ ...formData, fonte_validacao: e.target.value })}
                  label="Fonte de Validação"
                >
                  <MenuItem value="HUMANA">Humana</MenuItem>
                  <MenuItem value="ESPECIALISTA">Especialista</MenuItem>
                  <MenuItem value="SISTEMA">Sistema</MenuItem>
                  <MenuItem value="IMPORTACAO">Importação</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="NCM Final"
                value={formData.ncm_final}
                onChange={(e) => setFormData({ ...formData, ncm_final: e.target.value })}
                fullWidth
                disabled={itemDialog.mode === 'view'}
                required
                inputProps={{ maxLength: 8 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="CEST Final"
                value={formData.cest_final}
                onChange={(e) => setFormData({ ...formData, cest_final: e.target.value })}
                fullWidth
                disabled={itemDialog.mode === 'view'}
                inputProps={{ maxLength: 9 }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Justificativa da Inclusão"
                value={formData.justificativa_inclusao}
                onChange={(e) => setFormData({ ...formData, justificativa_inclusao: e.target.value })}
                fullWidth
                multiline
                rows={2}
                disabled={itemDialog.mode === 'view'}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="Score de Qualidade"
                type="number"
                value={formData.qualidade_score}
                onChange={(e) => setFormData({ ...formData, qualidade_score: parseFloat(e.target.value) })}
                fullWidth
                disabled={itemDialog.mode === 'view'}
                inputProps={{ min: 0, max: 1, step: 0.1 }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setItemDialog({ open: false, mode: 'create', item: null })}>
            {itemDialog.mode === 'view' ? 'Fechar' : 'Cancelar'}
          </Button>
          {itemDialog.mode !== 'view' && (
            <Button variant="contained" onClick={handleSaveItem} startIcon={<SaveIcon />}>
              {itemDialog.mode === 'create' ? 'Adicionar' : 'Salvar'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Dialog de Confirmação de Exclusão */}
      <Dialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, item: null })}
      >
        <DialogTitle>Confirmar Exclusão</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Tem certeza que deseja remover este item da base padrão?
          </Typography>
          {deleteDialog.item && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              <strong>Produto:</strong> {deleteDialog.item.descricao_produto}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, item: null })}>
            Cancelar
          </Button>
          <Button variant="contained" color="error" onClick={handleDeleteItem}>
            Excluir
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar para notificações */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
      />
    </Box>
  );
}

export default BasePadrao;
