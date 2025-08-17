import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  IconButton,
  Menu,
  MenuItem,
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
  Fab,
  Alert,
  LinearProgress,
  Avatar,
  Tooltip,
  Badge,
  Tabs,
  Tab,
  CircularProgress,
  Snackbar,
  Checkbox,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  MoreVert as MoreIcon,
  Category as CategoryIcon,
  Inventory as InventoryIcon,
  Barcode as BarcodeIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  AutoAwesome as AIIcon,
  Refresh as RefreshIcon,
  PlayArrow as ClassifyIcon,
  Replay as ReclassifyIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useEmpresa } from '../../contexts/EmpresaContext';
import axios from 'axios';

// API Base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

function Produtos() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const { empresaAtual } = useEmpresa();

  // Estados principais
  const [produtos, setProdutos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Estados da interface
  const [tabValue, setTabValue] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);

  // Estados dos diálogos
  const [productDialog, setProductDialog] = useState({ open: false, product: null });
  const [classificationDialog, setClassificationDialog] = useState({ open: false, products: [] });
  const [batchActionLoading, setBatchActionLoading] = useState(false);

  // Filtros baseados nas abas
  const tabs = [
    { label: 'Todos', value: '', badge: 0 },
    { label: 'A Classificar', value: 'nao_classificado', badge: 0 },
    { label: 'Classificados', value: 'classificado', badge: 0 },
    { label: 'Pendentes', value: 'pendente', badge: 0 },
  ];

  // Função para buscar produtos
  const fetchProdutos = async (status = '', search = '', pageNum = 0) => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: pageNum + 1,
        limit: rowsPerPage,
        ...(status && { status }),
        ...(search && { search }),
      };

      const response = await axios.get(`${API_BASE_URL}/produtos`, { params });
      
      setProdutos(response.data.produtos);
      setTotalCount(response.data.pagination.total);

      // Atualizar badges das abas baseado nos dados
      // Esta lógica pode ser melhorada com um endpoint específico para contadores
      
    } catch (err) {
      console.error('Erro ao buscar produtos:', err);
      setError('Erro ao carregar produtos. Verifique se a API está rodando.');
      
      // Fallback para dados mock
      setProdutos([
        {
          produto_id: 1,
          descricao_produto: 'Smartphone Samsung Galaxy S24',
          ncm_sugerido: '85171200',
          cest_sugerido: '21.001.00',
          status_revisao: 'APROVADO',
          status_classificacao: 'classificado',
          confianca_sugerida: 0.96,
          data_criacao: '2024-03-01T10:00:00'
        },
        {
          produto_id: 2,
          descricao_produto: 'Tênis Nike Air Max 270',
          ncm_sugerido: null,
          cest_sugerido: null,
          status_revisao: 'PENDENTE',
          status_classificacao: 'nao_classificado',
          confianca_sugerida: null,
          data_criacao: '2024-03-01T11:00:00'
        }
      ]);
      setTotalCount(2);
    } finally {
      setLoading(false);
    }
  };

  // Effect para carregar dados quando parâmetros mudarem
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const statusFromUrl = urlParams.get('status') || '';
    
    // Definir aba baseada na URL
    const tabIndex = tabs.findIndex(tab => tab.value === statusFromUrl);
    if (tabIndex >= 0) {
      setTabValue(tabIndex);
    }

    fetchProdutos(statusFromUrl, searchTerm, page);
  }, [location.search, searchTerm, page, rowsPerPage]);

  // Função para classificar produto individual
  const handleClassifyProduct = async (productId, forceReclassify = false) => {
    try {
      setBatchActionLoading(true);
      
      const response = await axios.post(
        `${API_BASE_URL}/produtos/${productId}/classificar`,
        null,
        { params: { force_reclassify: forceReclassify } }
      );

      setSnackbar({
        open: true,
        message: response.data.message,
        severity: 'success'
      });

      // Recarregar produtos após alguns segundos
      setTimeout(() => {
        fetchProdutos(tabs[tabValue].value, searchTerm, page);
      }, 2000);

    } catch (err) {
      console.error('Erro ao classificar produto:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao iniciar classificação',
        severity: 'error'
      });
    } finally {
      setBatchActionLoading(false);
    }
  };

  // Função para classificação em lote
  const handleBatchClassification = async () => {
    if (selectedProducts.length === 0) return;

    try {
      setBatchActionLoading(true);
      
      // Para cada produto selecionado, iniciar classificação
      const promises = selectedProducts.map(productId =>
        axios.post(`${API_BASE_URL}/produtos/${productId}/classificar`)
      );

      await Promise.all(promises);

      setSnackbar({
        open: true,
        message: `Classificação iniciada para ${selectedProducts.length} produtos`,
        severity: 'success'
      });

      setSelectedProducts([]);
      setClassificationDialog({ open: false, products: [] });

      // Recarregar após alguns segundos
      setTimeout(() => {
        fetchProdutos(tabs[tabValue].value, searchTerm, page);
      }, 2000);

    } catch (err) {
      console.error('Erro na classificação em lote:', err);
      setSnackbar({
        open: true,
        message: 'Erro na classificação em lote',
        severity: 'error'
      });
    } finally {
      setBatchActionLoading(false);
    }
  };

  // Função para mudança de aba
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setPage(0);
    setSelectedProducts([]);
    
    const status = tabs[newValue].value;
    const url = status ? `/produtos?status=${status}` : '/produtos';
    navigate(url);
  };

  // Função para busca
  const handleSearch = (event) => {
    if (event.key === 'Enter' || event.type === 'click') {
      setPage(0);
      fetchProdutos(tabs[tabValue].value, searchTerm, 0);
    }
  };

  // Renderizar status do produto
  const renderProductStatus = (produto) => {
    if (produto.status_classificacao === 'classificado') {
      return (
        <Chip
          icon={<SuccessIcon />}
          label="Classificado"
          color="success"
          size="small"
        />
      );
    } else {
      return (
        <Chip
          icon={<WarningIcon />}
          label="Pendente"
          color="warning"
          size="small"
        />
      );
    }
  };

  // Renderizar confiança
  const renderConfidence = (confidence) => {
    if (!confidence) return '-';
    
    const percentage = Math.round(confidence * 100);
    const color = percentage >= 90 ? 'success' : percentage >= 70 ? 'warning' : 'error';
    
    return (
      <Chip
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
          Gestão de Produtos
        </Typography>
        
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Gerencie o catálogo de produtos e suas classificações fiscais
        </Typography>

        {/* Controles */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2 }}>
          <TextField
            placeholder="Buscar produtos..."
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
            onClick={() => fetchProdutos(tabs[tabValue].value, searchTerm, page)}
            disabled={loading}
          >
            Atualizar
          </Button>

          {selectedProducts.length > 0 && (
            <Button
              variant="contained"
              startIcon={<ClassifyIcon />}
              onClick={() => setClassificationDialog({ open: true, products: selectedProducts })}
              disabled={batchActionLoading}
            >
              Classificar Selecionados ({selectedProducts.length})
            </Button>
          )}
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Card sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="fullWidth"
        >
          {tabs.map((tab, index) => (
            <Tab
              key={index}
              label={
                <Badge badgeContent={tab.badge} color="error">
                  {tab.label}
                </Badge>
              }
            />
          ))}
        </Tabs>
      </Card>

      {/* Tabela de Produtos */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          {loading && <LinearProgress />}
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      indeterminate={selectedProducts.length > 0 && selectedProducts.length < produtos.length}
                      checked={produtos.length > 0 && selectedProducts.length === produtos.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedProducts(produtos.map(p => p.produto_id));
                        } else {
                          setSelectedProducts([]);
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell>Produto</TableCell>
                  <TableCell>NCM</TableCell>
                  <TableCell>CEST</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Confiança</TableCell>
                  <TableCell>Data</TableCell>
                  <TableCell>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {produtos.map((produto) => (
                  <TableRow key={produto.produto_id} hover>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedProducts.includes(produto.produto_id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedProducts([...selectedProducts, produto.produto_id]);
                          } else {
                            setSelectedProducts(selectedProducts.filter(id => id !== produto.produto_id));
                          }
                        }}
                      />
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Avatar sx={{ bgcolor: 'primary.light' }}>
                          <InventoryIcon />
                        </Avatar>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {produto.descricao_produto}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ID: {produto.produto_id}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      {produto.ncm_sugerido || '-'}
                    </TableCell>
                    
                    <TableCell>
                      {produto.cest_sugerido || '-'}
                    </TableCell>
                    
                    <TableCell>
                      {renderProductStatus(produto)}
                    </TableCell>
                    
                    <TableCell>
                      {renderConfidence(produto.confianca_sugerida)}
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(produto.data_criacao).toLocaleDateString('pt-BR')}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="Ver detalhes">
                          <IconButton
                            size="small"
                            onClick={() => setProductDialog({ open: true, product: produto })}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title={produto.status_classificacao === 'classificado' ? 'Reclassificar' : 'Classificar'}>
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleClassifyProduct(
                              produto.produto_id, 
                              produto.status_classificacao === 'classificado'
                            )}
                            disabled={batchActionLoading}
                          >
                            {produto.status_classificacao === 'classificado' ? <ReclassifyIcon /> : <ClassifyIcon />}
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

      {/* Dialog de Detalhes do Produto */}
      <Dialog
        open={productDialog.open}
        onClose={() => setProductDialog({ open: false, product: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Detalhes do Produto
        </DialogTitle>
        <DialogContent>
          {productDialog.product && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  {productDialog.product.descricao_produto}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  ID do Produto
                </Typography>
                <Typography variant="body1">
                  {productDialog.product.produto_id}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
                {renderProductStatus(productDialog.product)}
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  NCM Sugerido
                </Typography>
                <Typography variant="body1">
                  {productDialog.product.ncm_sugerido || 'Não classificado'}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  CEST Sugerido
                </Typography>
                <Typography variant="body1">
                  {productDialog.product.cest_sugerido || 'Não classificado'}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Confiança
                </Typography>
                {renderConfidence(productDialog.product.confianca_sugerida)}
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Data de Criação
                </Typography>
                <Typography variant="body1">
                  {new Date(productDialog.product.data_criacao).toLocaleString('pt-BR')}
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProductDialog({ open: false, product: null })}>
            Fechar
          </Button>
          {productDialog.product && (
            <Button
              variant="contained"
              startIcon={productDialog.product.status_classificacao === 'classificado' ? <ReclassifyIcon /> : <ClassifyIcon />}
              onClick={() => {
                handleClassifyProduct(
                  productDialog.product.produto_id,
                  productDialog.product.status_classificacao === 'classificado'
                );
                setProductDialog({ open: false, product: null });
              }}
            >
              {productDialog.product.status_classificacao === 'classificado' ? 'Reclassificar' : 'Classificar'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Dialog de Classificação em Lote */}
      <Dialog
        open={classificationDialog.open}
        onClose={() => setClassificationDialog({ open: false, products: [] })}
      >
        <DialogTitle>
          Classificação em Lote
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Deseja iniciar a classificação para {selectedProducts.length} produtos selecionados?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Este processo pode levar alguns minutos para ser concluído.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClassificationDialog({ open: false, products: [] })}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleBatchClassification}
            disabled={batchActionLoading}
            startIcon={batchActionLoading ? <CircularProgress size={16} /> : <ClassifyIcon />}
          >
            {batchActionLoading ? 'Processando...' : 'Classificar'}
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

export default Produtos;
