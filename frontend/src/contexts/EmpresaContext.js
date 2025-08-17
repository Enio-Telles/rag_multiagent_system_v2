import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { empresaService } from '../services/empresaService';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

// Estado inicial
const initialState = {
  empresas: [],
  selectedEmpresa: null,
  isLoadingEmpresas: false,
  error: null,
};

// Actions
const EMPRESA_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_EMPRESAS: 'SET_EMPRESAS',
  SET_SELECTED_EMPRESA: 'SET_SELECTED_EMPRESA',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  UPDATE_EMPRESA: 'UPDATE_EMPRESA',
  ADD_EMPRESA: 'ADD_EMPRESA',
  REMOVE_EMPRESA: 'REMOVE_EMPRESA',
};

// Reducer
function empresaReducer(state, action) {
  switch (action.type) {
    case EMPRESA_ACTIONS.SET_LOADING:
      return {
        ...state,
        isLoadingEmpresas: action.payload,
      };
    
    case EMPRESA_ACTIONS.SET_EMPRESAS:
      return {
        ...state,
        empresas: action.payload,
        isLoadingEmpresas: false,
        error: null,
      };
    
    case EMPRESA_ACTIONS.SET_SELECTED_EMPRESA:
      return {
        ...state,
        selectedEmpresa: action.payload,
      };
    
    case EMPRESA_ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        isLoadingEmpresas: false,
      };
    
    case EMPRESA_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };
    
    case EMPRESA_ACTIONS.UPDATE_EMPRESA:
      return {
        ...state,
        empresas: state.empresas.map(empresa =>
          empresa.id === action.payload.id ? action.payload : empresa
        ),
        selectedEmpresa: state.selectedEmpresa?.id === action.payload.id
          ? action.payload
          : state.selectedEmpresa,
      };
    
    case EMPRESA_ACTIONS.ADD_EMPRESA:
      return {
        ...state,
        empresas: [...state.empresas, action.payload],
      };
    
    case EMPRESA_ACTIONS.REMOVE_EMPRESA:
      return {
        ...state,
        empresas: state.empresas.filter(empresa => empresa.id !== action.payload),
        selectedEmpresa: state.selectedEmpresa?.id === action.payload
          ? null
          : state.selectedEmpresa,
      };
    
    default:
      return state;
  }
}

// Context
const EmpresaContext = createContext();

// Provider
export function EmpresaProvider({ children }) {
  const [state, dispatch] = useReducer(empresaReducer, initialState);
  const { isAuthenticated, user, updatePermissions } = useAuth();

  // Carregar empresas quando autenticado
  useEffect(() => {
    if (isAuthenticated && user) {
      loadEmpresas();
      restoreSelectedEmpresa();
    }
  }, [isAuthenticated, user]);

  const loadEmpresas = async () => {
    try {
      dispatch({ type: EMPRESA_ACTIONS.SET_LOADING, payload: true });
      
      const response = await empresaService.getEmpresas();
      
      if (response.success) {
        dispatch({
          type: EMPRESA_ACTIONS.SET_EMPRESAS,
          payload: response.empresas || [],
        });
      } else {
        throw new Error(response.message || 'Erro ao carregar empresas');
      }
    } catch (error) {
      console.error('Erro ao carregar empresas:', error);
      dispatch({
        type: EMPRESA_ACTIONS.SET_ERROR,
        payload: error.message,
      });
      toast.error('Erro ao carregar empresas');
    }
  };

  const restoreSelectedEmpresa = () => {
    const savedEmpresa = localStorage.getItem('selected_empresa');
    if (savedEmpresa) {
      try {
        const empresa = JSON.parse(savedEmpresa);
        dispatch({
          type: EMPRESA_ACTIONS.SET_SELECTED_EMPRESA,
          payload: empresa,
        });
      } catch (error) {
        console.error('Erro ao restaurar empresa selecionada:', error);
        localStorage.removeItem('selected_empresa');
      }
    }
  };

  const selectEmpresa = async (empresa) => {
    try {
      // Verificar se o usuário tem acesso à empresa
      if (!canAccessEmpresa(empresa.id)) {
        toast.error('Você não tem permissão para acessar esta empresa');
        return false;
      }

      // Salvar no localStorage
      localStorage.setItem('selected_empresa', JSON.stringify(empresa));
      
      dispatch({
        type: EMPRESA_ACTIONS.SET_SELECTED_EMPRESA,
        payload: empresa,
      });

      // Carregar permissões específicas da empresa
      await loadEmpresaPermissions(empresa.id);
      
      toast.success(`Empresa ${empresa.nome} selecionada`);
      return true;
    } catch (error) {
      console.error('Erro ao selecionar empresa:', error);
      toast.error('Erro ao selecionar empresa');
      return false;
    }
  };

  const loadEmpresaPermissions = async (empresaId) => {
    try {
      const response = await empresaService.getUserPermissions(empresaId);
      
      if (response.success) {
        updatePermissions(response.permissions);
      }
    } catch (error) {
      console.error('Erro ao carregar permissões da empresa:', error);
    }
  };

  const canAccessEmpresa = (empresaId) => {
    if (!user || !user.empresas) return false;
    
    return user.empresas.some(empresa => 
      empresa.id === empresaId && empresa.ativa
    );
  };

  const createEmpresa = async (empresaData) => {
    try {
      const response = await empresaService.createEmpresa(empresaData);
      
      if (response.success) {
        dispatch({
          type: EMPRESA_ACTIONS.ADD_EMPRESA,
          payload: response.empresa,
        });
        
        toast.success('Empresa criada com sucesso!');
        return { success: true, empresa: response.empresa };
      } else {
        throw new Error(response.message || 'Erro ao criar empresa');
      }
    } catch (error) {
      console.error('Erro ao criar empresa:', error);
      toast.error(error.message || 'Erro ao criar empresa');
      return { success: false, error: error.message };
    }
  };

  const updateEmpresa = async (empresaId, empresaData) => {
    try {
      const response = await empresaService.updateEmpresa(empresaId, empresaData);
      
      if (response.success) {
        dispatch({
          type: EMPRESA_ACTIONS.UPDATE_EMPRESA,
          payload: response.empresa,
        });
        
        toast.success('Empresa atualizada com sucesso!');
        return { success: true, empresa: response.empresa };
      } else {
        throw new Error(response.message || 'Erro ao atualizar empresa');
      }
    } catch (error) {
      console.error('Erro ao atualizar empresa:', error);
      toast.error(error.message || 'Erro ao atualizar empresa');
      return { success: false, error: error.message };
    }
  };

  const deleteEmpresa = async (empresaId) => {
    try {
      const response = await empresaService.deleteEmpresa(empresaId);
      
      if (response.success) {
        dispatch({
          type: EMPRESA_ACTIONS.REMOVE_EMPRESA,
          payload: empresaId,
        });
        
        toast.success('Empresa removida com sucesso!');
        return { success: true };
      } else {
        throw new Error(response.message || 'Erro ao remover empresa');
      }
    } catch (error) {
      console.error('Erro ao remover empresa:', error);
      toast.error(error.message || 'Erro ao remover empresa');
      return { success: false, error: error.message };
    }
  };

  const clearSelectedEmpresa = () => {
    localStorage.removeItem('selected_empresa');
    dispatch({
      type: EMPRESA_ACTIONS.SET_SELECTED_EMPRESA,
      payload: null,
    });
  };

  const refreshEmpresas = () => {
    loadEmpresas();
  };

  const clearError = () => {
    dispatch({ type: EMPRESA_ACTIONS.CLEAR_ERROR });
  };

  const value = {
    // Estado
    empresas: state.empresas,
    selectedEmpresa: state.selectedEmpresa,
    isLoadingEmpresas: state.isLoadingEmpresas,
    error: state.error,
    
    // Ações
    selectEmpresa,
    createEmpresa,
    updateEmpresa,
    deleteEmpresa,
    clearSelectedEmpresa,
    refreshEmpresas,
    clearError,
    canAccessEmpresa,
    
    // Helpers
    hasSelectedEmpresa: !!state.selectedEmpresa,
    userEmpresas: user?.empresas || [],
  };

  return (
    <EmpresaContext.Provider value={value}>
      {children}
    </EmpresaContext.Provider>
  );
}

// Hook
export function useEmpresa() {
  const context = useContext(EmpresaContext);
  if (!context) {
    throw new Error('useEmpresa deve ser usado dentro de EmpresaProvider');
  }
  return context;
}
