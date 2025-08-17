import axios from 'axios';

// Configuração base da API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Instância do axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratar respostas
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Se token expirou ou é inválido
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      localStorage.removeItem('selected_empresa');
      
      // Redirecionar para login se não estiver já lá
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Funções utilitárias
export const apiClient = {
  // GET request
  get: async (url, config = {}) => {
    try {
      const response = await api.get(url, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // POST request
  post: async (url, data = {}, config = {}) => {
    try {
      const response = await api.post(url, data, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // PUT request
  put: async (url, data = {}, config = {}) => {
    try {
      const response = await api.put(url, data, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // PATCH request
  patch: async (url, data = {}, config = {}) => {
    try {
      const response = await api.patch(url, data, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // DELETE request
  delete: async (url, config = {}) => {
    try {
      const response = await api.delete(url, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // Upload de arquivo
  upload: async (url, formData, onProgress = null) => {
    try {
      const config = {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      };

      if (onProgress) {
        config.onUploadProgress = (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        };
      }

      const response = await api.post(url, formData, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
};

// Tratamento de erros da API
function handleApiError(error) {
  let message = 'Erro inesperado';
  let code = 'UNKNOWN_ERROR';
  let details = null;

  if (error.response) {
    // Resposta recebida do servidor com status de erro
    const { status, data } = error.response;
    
    message = data?.message || data?.detail || `Erro ${status}`;
    code = data?.code || `HTTP_${status}`;
    details = data?.details || null;

    // Mensagens específicas por status
    switch (status) {
      case 400:
        message = data?.message || 'Dados inválidos';
        break;
      case 401:
        message = 'Não autorizado - faça login novamente';
        break;
      case 403:
        message = 'Acesso negado - permissões insuficientes';
        break;
      case 404:
        message = 'Recurso não encontrado';
        break;
      case 409:
        message = data?.message || 'Conflito de dados';
        break;
      case 422:
        message = 'Dados inválidos';
        details = data?.errors || data?.validation_errors;
        break;
      case 429:
        message = 'Muitas requisições - tente novamente em alguns minutos';
        break;
      case 500:
        message = 'Erro interno do servidor';
        break;
      case 502:
        message = 'Servidor indisponível';
        break;
      case 503:
        message = 'Serviço temporariamente indisponível';
        break;
      default:
        message = `Erro ${status}: ${message}`;
    }
  } else if (error.request) {
    // Requisição foi feita mas não houve resposta
    message = 'Erro de conexão - verifique sua internet';
    code = 'NETWORK_ERROR';
  } else {
    // Erro na configuração da requisição
    message = error.message || 'Erro na configuração da requisição';
    code = 'CONFIG_ERROR';
  }

  const apiError = new Error(message);
  apiError.code = code;
  apiError.details = details;
  apiError.originalError = error;

  return apiError;
}

// Utilitários para URLs
export const buildUrl = (endpoint, params = {}) => {
  const url = new URL(endpoint, API_BASE_URL);
  
  Object.keys(params).forEach(key => {
    if (params[key] !== null && params[key] !== undefined) {
      url.searchParams.append(key, params[key]);
    }
  });
  
  return url.toString();
};

// Utilitários para headers
export const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Utilitários para empresa
export const getEmpresaHeaders = () => {
  const empresa = localStorage.getItem('selected_empresa');
  if (empresa) {
    try {
      const empresaData = JSON.parse(empresa);
      return { 'X-Empresa-ID': empresaData.id };
    } catch (error) {
      console.error('Erro ao parser empresa:', error);
    }
  }
  return {};
};

// Headers combinados
export const getDefaultHeaders = () => {
  return {
    ...getAuthHeaders(),
    ...getEmpresaHeaders(),
    'Content-Type': 'application/json',
  };
};

// Validador de resposta
export const validateResponse = (response) => {
  if (!response) {
    throw new Error('Resposta vazia da API');
  }
  
  if (response.success === false) {
    throw new Error(response.message || 'Erro na operação');
  }
  
  return response;
};

// Debounce para requests
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Cache simples para requests
class SimpleCache {
  constructor(maxSize = 100, ttl = 300000) { // 5 minutos default
    this.cache = new Map();
    this.maxSize = maxSize;
    this.ttl = ttl;
  }

  get(key) {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }

  set(key, data) {
    if (this.cache.size >= this.maxSize) {
      // Remove o primeiro item (LRU simples)
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  clear() {
    this.cache.clear();
  }

  delete(key) {
    this.cache.delete(key);
  }
}

export const apiCache = new SimpleCache();

// Request com cache
export const cachedRequest = async (key, requestFn, useCache = true) => {
  if (useCache) {
    const cached = apiCache.get(key);
    if (cached) {
      return cached;
    }
  }
  
  const result = await requestFn();
  
  if (useCache) {
    apiCache.set(key, result);
  }
  
  return result;
};

export default api;
