import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authService } from '../services/authService';
import toast from 'react-hot-toast';

// Estado inicial
const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  permissions: {},
};

// Actions
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  RESTORE_SESSION: 'RESTORE_SESSION',
  UPDATE_PERMISSIONS: 'UPDATE_PERMISSIONS',
  SET_LOADING: 'SET_LOADING',
};

// Reducer
function authReducer(state, action) {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
      return {
        ...state,
        isLoading: true,
      };
    
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        permissions: action.payload.permissions || {},
      };
    
    case AUTH_ACTIONS.LOGIN_FAILURE:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        permissions: {},
      };
    
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        permissions: {},
      };
    
    case AUTH_ACTIONS.RESTORE_SESSION:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        permissions: action.payload.permissions || {},
      };
    
    case AUTH_ACTIONS.UPDATE_PERMISSIONS:
      return {
        ...state,
        permissions: action.payload,
      };
    
    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload,
      };
    
    default:
      return state;
  }
}

// Context
const AuthContext = createContext();

// Provider
export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Restaurar sessão ao carregar
  useEffect(() => {
    restoreSession();
  }, []);

  const restoreSession = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const user = localStorage.getItem('auth_user');
      
      if (token && user) {
        const userData = JSON.parse(user);
        
        // Verificar se token ainda é válido
        const isValid = await authService.validateToken(token);
        
        if (isValid) {
          dispatch({
            type: AUTH_ACTIONS.RESTORE_SESSION,
            payload: {
              user: userData,
              token: token,
              permissions: userData.permissions || {},
            },
          });
        } else {
          // Token inválido, limpar storage
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
          dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
        }
      } else {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      }
    } catch (error) {
      console.error('Erro ao restaurar sessão:', error);
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
    }
  };

  const login = async (credentials) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });
      
      const response = await authService.login(credentials);
      
      if (response.success) {
        // Salvar no localStorage
        localStorage.setItem('auth_token', response.token);
        localStorage.setItem('auth_user', JSON.stringify(response.user));
        
        dispatch({
          type: AUTH_ACTIONS.LOGIN_SUCCESS,
          payload: {
            user: response.user,
            token: response.token,
            permissions: response.user.permissions || {},
          },
        });
        
        toast.success('Login realizado com sucesso!');
        return { success: true };
      } else {
        throw new Error(response.message || 'Erro no login');
      }
    } catch (error) {
      dispatch({ type: AUTH_ACTIONS.LOGIN_FAILURE });
      toast.error(error.message || 'Erro ao realizar login');
      return { success: false, error: error.message };
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Erro ao fazer logout no servidor:', error);
    } finally {
      // Limpar dados locais independente do resultado do servidor
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      localStorage.removeItem('selected_empresa');
      
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
      toast.success('Logout realizado com sucesso!');
    }
  };

  const updatePermissions = (permissions) => {
    dispatch({
      type: AUTH_ACTIONS.UPDATE_PERMISSIONS,
      payload: permissions,
    });
    
    // Atualizar também no localStorage
    if (state.user) {
      const updatedUser = { ...state.user, permissions };
      localStorage.setItem('auth_user', JSON.stringify(updatedUser));
    }
  };

  const hasPermission = (permission) => {
    return state.permissions[permission] === true;
  };

  const value = {
    // Estado
    user: state.user,
    token: state.token,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    permissions: state.permissions,
    
    // Ações
    login,
    logout,
    updatePermissions,
    hasPermission,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return context;
}
