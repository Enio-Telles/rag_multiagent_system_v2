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
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useEmpresa } from '../../contexts/EmpresaContext';

// Mock data - em produção virá da API
const mockProdutos = [
  {
    id: 1,
    nome: 'Smartphone Samsung Galaxy S23 Ultra',
    descricao: 'Smartphone premium com câmera de 200MP e S Pen',
    codigo_barras: '7893123456789',
    categoria: 'Eletrônicos',
    ncm: '85171200',
    cest: '2140300',
    status: 'ativo',
    classificacao_status: 'aprovado',
    confianca_ia: 96.5,
    preco: 4999.99,
    data_criacao: '2024-01-15',
    ultima_atualizacao: '2024-03-10',
  },
  {
    id: 2,
    nome: 'Tênis Nike Air Max 270',
    descricao: 'Tênis esportivo masculino com tecnologia Air Max',
    codigo_barras: '7891234567890',
    categoria: 'Calçados',
    ncm: '64041100',
    cest: '2840100',
    status: 'ativo',
    classificacao_status: 'pendente',
    confianca_ia: 87.3,
    preco: 899.99,
    data_criacao: '2024-02-20',
    ultima_atualizacao: '2024-03-12',
  },
  {
    id: 3,
    nome: 'Livro JavaScript: O Guia Definitivo',
    descricao: 'Guia completo para programação JavaScript moderna',
    codigo_barras: '9788563308047',
    categoria: 'Livros',
    ncm: '49019900',
    cest: null,
    status: 'ativo',
    classificacao_status: 'rejeitado',
    confianca_ia: 45.2,
    preco: 129.90,
    data_criacao: '2024-03-01',
    ultima_atualizacao: '2024-03-11',
  },
];

const statusColors = {
  ativo: 'success',
  inativo: 'default',
  pendente: 'warning',
};

const classificacaoColors = {
  aprovado: 'success',
  pendente: 'warning',
  rejeitado: 'error',
  nao_classificado: 'default',
};

function Produtos() {
  const navigate = useNavigate();
  const { empresaAtual } = useEmpresa();
  
  const [produtos, setProdutos] = useState(mockProdutos);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAnchor, setFilterAnchor] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);

  // Filtros
  const [filters, setFilters] = useState({
    status: 'todos',
    classificacao: 'todos',
    categoria: 'todas',
  });

  useEffect(() => {
    // Simular carregamento de dados
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, [empresaAtual]);

  // Filtrar produtos
  const filteredProdutos = produtos.filter(produto => {
    const matchSearch = produto.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       produto.codigo_barras.includes(searchTerm) ||
                       produto.categoria.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchStatus = filters.status === 'todos' || produto.status === filters.status;
    const matchClassificacao = filters.classificacao === 'todos' || produto.classificacao_status === filters.classificacao;
    const matchCategoria = filters.categoria === 'todas' || produto.categoria === filters.categoria;

    return matchSearch && matchStatus && matchClassificacao && matchCategoria;
  });

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleViewDetails = (produto) => {
    setSelectedProduct(produto);
    setDetailsOpen(true);
  };

  const handleClassifyProduct = (produto) => {
    navigate(`/classificacao?produto=${produto.id}`);
  };

  const getConfiancaColor = (confianca) => {
    if (confianca >= 90) return 'success';
    if (confianca >= 70) return 'warning';
    return 'error';
  };

  const getConfiancaIcon = (confianca) => {
    if (confianca >= 90) return <SuccessIcon />;
    if (confianca >= 70) return <WarningIcon />;
    return <ErrorIcon />;
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Gestão de Produtos
        </Typography>
        
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Gerencie o catálogo de produtos da {empresaAtual?.nome}
        </Typography>

        {/* Estatísticas rápidas */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.light', mx: 'auto', mb: 1 }}>
                  <InventoryIcon color="primary" />
                </Avatar>
                <Typography variant="h6" fontWeight="bold">
                  {produtos.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total de Produtos
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'success.light', mx: 'auto', mb: 1 }}>
                  <SuccessIcon color="success" />
                </Avatar>
                <Typography variant="h6" fontWeight="bold">
                  {produtos.filter(p => p.classificacao_status === 'aprovado').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Classificados
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.light', mx: 'auto', mb: 1 }}>
                  <WarningIcon color="warning" />
                </Avatar>
                <Typography variant="h6" fontWeight="bold">
                  {produtos.filter(p => p.classificacao_status === 'pendente').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Pendentes
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'info.light', mx: 'auto', mb: 1 }}>
                  <AIIcon color="info" />
                </Avatar>
                <Typography variant="h6" fontWeight="bold">
                  {Math.round(produtos.reduce((acc, p) => acc + p.confianca_ia, 0) / produtos.length)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Precisão Média IA
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Filtros e Busca */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Buscar produtos por nome, código de barras ou categoria..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                <Button
                  startIcon={<FilterIcon />}
                  onClick={(e) => setFilterAnchor(e.currentTarget)}
                  variant="outlined"
                >
                  Filtros
                </Button>
                
                <Button
                  startIcon={<UploadIcon />}
                  onClick={() => setUploadOpen(true)}
                  variant="outlined"
                >
                  Importar
                </Button>
                
                <Button
                  startIcon={<DownloadIcon />}
                  variant="outlined"
                >
                  Exportar
                </Button>
                
                <Button
                  startIcon={<AddIcon />}
                  variant="contained"
                  onClick={() => navigate('/produtos/novo')}
                >
                  Novo Produto
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabela de Produtos */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            <Box sx={{ p: 3 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Carregando produtos...
              </Typography>
            </Box>
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Produto</TableCell>
                      <TableCell>Categoria</TableCell>
                      <TableCell>Código de Barras</TableCell>
                      <TableCell>Classificação</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Confiança IA</TableCell>
                      <TableCell>Preço</TableCell>
                      <TableCell align="center">Ações</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredProdutos
                      .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                      .map((produto) => (
                        <TableRow key={produto.id} hover>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {produto.nome}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {produto.descricao.substring(0, 50)}...
                              </Typography>
                            </Box>
                          </TableCell>
                          
                          <TableCell>
                            <Chip
                              label={produto.categoria}
                              size="small"
                              variant="outlined"
                              icon={<CategoryIcon />}
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <BarcodeIcon fontSize="small" />
                              <Typography variant="body2" fontFamily="monospace">
                                {produto.codigo_barras}
                              </Typography>
                            </Box>
                          </TableCell>
                          
                          <TableCell>
                            <Chip
                              label={produto.classificacao_status}
                              size="small"
                              color={classificacaoColors[produto.classificacao_status]}
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Chip
                              label={produto.status}
                              size="small"
                              color={statusColors[produto.status]}
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip
                                icon={getConfiancaIcon(produto.confianca_ia)}
                                label={`${produto.confianca_ia}%`}
                                size="small"
                                color={getConfiancaColor(produto.confianca_ia)}
                              />
                            </Box>
                          </TableCell>
                          
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              R$ {produto.preco.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                            </Typography>
                          </TableCell>
                          
                          <TableCell align="center">
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              <Tooltip title="Ver detalhes">
                                <IconButton
                                  size="small"
                                  onClick={() => handleViewDetails(produto)}
                                >
                                  <ViewIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              
                              <Tooltip title="Editar">
                                <IconButton
                                  size="small"
                                  onClick={() => navigate(`/produtos/${produto.id}/editar`)}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              
                              <Tooltip title="Classificar com IA">
                                <IconButton
                                  size="small"
                                  onClick={() => handleClassifyProduct(produto)}
                                  color="primary"
                                >
                                  <AIIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
              
              <TablePagination
                rowsPerPageOptions={[5, 10, 25, 50]}
                component="div"
                count={filteredProdutos.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                labelRowsPerPage="Produtos por página:"
              />
            </>
          )}
        </CardContent>
      </Card>

      {/* Menu de Filtros */}
      <Menu
        anchorEl={filterAnchor}
        open={Boolean(filterAnchor)}
        onClose={() => setFilterAnchor(null)}
      >
        <MenuItem onClick={() => setFilterAnchor(null)}>
          Status: Todos
        </MenuItem>
        <MenuItem onClick={() => setFilterAnchor(null)}>
          Status: Ativos
        </MenuItem>
        <MenuItem onClick={() => setFilterAnchor(null)}>
          Status: Inativos
        </MenuItem>
      </Menu>

      {/* Dialog de Detalhes do Produto */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Detalhes do Produto
        </DialogTitle>
        <DialogContent>
          {selectedProduct && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  {selectedProduct.nome}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {selectedProduct.descricao}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2">Código de Barras:</Typography>
                <Typography variant="body2">{selectedProduct.codigo_barras}</Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2">Categoria:</Typography>
                <Typography variant="body2">{selectedProduct.categoria}</Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2">NCM:</Typography>
                <Typography variant="body2">{selectedProduct.ncm}</Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2">CEST:</Typography>
                <Typography variant="body2">{selectedProduct.cest || 'N/A'}</Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2">Confiança IA:</Typography>
                <Chip
                  label={`${selectedProduct.confianca_ia}%`}
                  color={getConfiancaColor(selectedProduct.confianca_ia)}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="subtitle2">Preço:</Typography>
                <Typography variant="body2">
                  R$ {selectedProduct.preco.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>
            Fechar
          </Button>
          <Button variant="contained" onClick={() => {
            setDetailsOpen(false);
            navigate(`/produtos/${selectedProduct.id}/editar`);
          }}>
            Editar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de Upload */}
      <Dialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Importar Produtos</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Faça upload de um arquivo Excel (.xlsx) ou CSV com os dados dos produtos.
          </Alert>
          <Box
            sx={{
              border: '2px dashed',
              borderColor: 'grey.300',
              borderRadius: 1,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': {
                borderColor: 'primary.main',
              },
            }}
          >
            <UploadIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
            <Typography variant="body1" gutterBottom>
              Clique para selecionar arquivo ou arraste aqui
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Formatos aceitos: .xlsx, .csv (máx. 10MB)
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadOpen(false)}>
            Cancelar
          </Button>
          <Button variant="contained">
            Fazer Upload
          </Button>
        </DialogActions>
      </Dialog>

      {/* FAB para ações rápidas */}
      <Fab
        color="primary"
        aria-label="classificar todos"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
        }}
        onClick={() => navigate('/classificacao')}
      >
        <Badge badgeContent={produtos.filter(p => p.classificacao_status === 'pendente').length} color="error">
          <AIIcon />
        </Badge>
      </Fab>
    </Box>
  );
}

export default Produtos;
