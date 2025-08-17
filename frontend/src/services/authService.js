import { apiClient, validateResponse } from './apiClient';

export const authService = {
  // Login
  login: async (credentials) => {
    try {
      const response = await apiClient.post('/api/v1/auth/login', {
        username: credentials.username,
        password: credentials.password,
      });
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Logout
  logout: async () => {
    try {
      const response = await apiClient.post('/api/v1/auth/logout');
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Refresh token
  refreshToken: async () => {
    try {
      const response = await apiClient.post('/api/v1/auth/refresh');
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Validar token
  validateToken: async (token) => {
    try {
      const response = await apiClient.get('/api/v1/auth/validate', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      return response.valid === true;
    } catch (error) {
      return false;
    }
  },

  // Obter perfil do usuário
  getProfile: async () => {
    try {
      const response = await apiClient.get('/api/v1/auth/profile');
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Atualizar perfil
  updateProfile: async (profileData) => {
    try {
      const response = await apiClient.put('/api/v1/auth/profile', profileData);
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Alterar senha
  changePassword: async (passwordData) => {
    try {
      const response = await apiClient.post('/api/v1/auth/change-password', {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword,
      });
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Recuperar senha
  forgotPassword: async (email) => {
    try {
      const response = await apiClient.post('/api/v1/auth/forgot-password', {
        email: email,
      });
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Reset senha
  resetPassword: async (resetData) => {
    try {
      const response = await apiClient.post('/api/v1/auth/reset-password', {
        token: resetData.token,
        new_password: resetData.newPassword,
        confirm_password: resetData.confirmPassword,
      });
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Verificar se usuário está autenticado
  isAuthenticated: () => {
    const token = localStorage.getItem('auth_token');
    const user = localStorage.getItem('auth_user');
    
    return !!(token && user);
  },

  // Obter token atual
  getCurrentToken: () => {
    return localStorage.getItem('auth_token');
  },

  // Obter usuário atual
  getCurrentUser: () => {
    const user = localStorage.getItem('auth_user');
    if (user) {
      try {
        return JSON.parse(user);
      } catch (error) {
        console.error('Erro ao parser usuário:', error);
        return null;
      }
    }
    return null;
  },
};
