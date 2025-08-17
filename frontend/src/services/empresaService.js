import { apiClient, validateResponse, getEmpresaHeaders } from './apiClient';

export const empresaService = {
  // Listar empresas do usuário
  getEmpresas: async () => {
    try {
      const response = await apiClient.get('/api/v1/empresas');
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Obter empresa específica
  getEmpresa: async (empresaId) => {
    try {
      const response = await apiClient.get(`/api/v1/empresas/${empresaId}`);
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Criar nova empresa
  createEmpresa: async (empresaData) => {
    try {
      const response = await apiClient.post('/api/v1/empresas', {
        nome: empresaData.nome,
        razao_social: empresaData.razaoSocial,
        cnpj: empresaData.cnpj,
        email: empresaData.email,
        telefone: empresaData.telefone,
        endereco: empresaData.endereco,
        configuracoes: empresaData.configuracoes || {},
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

  // Atualizar empresa
  updateEmpresa: async (empresaId, empresaData) => {
    try {
      const response = await apiClient.put(`/api/v1/empresas/${empresaId}`, {
        nome: empresaData.nome,
        razao_social: empresaData.razaoSocial,
        cnpj: empresaData.cnpj,
        email: empresaData.email,
        telefone: empresaData.telefone,
        endereco: empresaData.endereco,
        configuracoes: empresaData.configuracoes,
        ativa: empresaData.ativa,
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

  // Deletar empresa
  deleteEmpresa: async (empresaId) => {
    try {
      const response = await apiClient.delete(`/api/v1/empresas/${empresaId}`);
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Obter permissões do usuário para empresa
  getUserPermissions: async (empresaId) => {
    try {
      const response = await apiClient.get(`/api/v1/empresas/${empresaId}/permissions`);
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
        permissions: {},
      };
    }
  },

  // Obter estatísticas da empresa
  getEmpresaStats: async (empresaId) => {
    try {
      const response = await apiClient.get(`/api/v1/empresas/${empresaId}/stats`, {
        headers: getEmpresaHeaders(),
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

  // Sincronizar dados da empresa
  syncEmpresaData: async (empresaId) => {
    try {
      const response = await apiClient.post(`/api/v1/empresas/${empresaId}/sync`, {}, {
        headers: getEmpresaHeaders(),
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

  // Backup da empresa
  backupEmpresa: async (empresaId) => {
    try {
      const response = await apiClient.post(`/api/v1/empresas/${empresaId}/backup`, {}, {
        headers: getEmpresaHeaders(),
        responseType: 'blob', // Para download de arquivo
      });
      
      return {
        success: true,
        data: response,
      };
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Importar dados para empresa
  importData: async (empresaId, file, onProgress = null) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await apiClient.upload(
        `/api/v1/empresas/${empresaId}/import`,
        formData,
        onProgress
      );
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Obter configurações da empresa
  getConfiguracoes: async (empresaId) => {
    try {
      const response = await apiClient.get(`/api/v1/empresas/${empresaId}/configuracoes`, {
        headers: getEmpresaHeaders(),
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

  // Atualizar configurações da empresa
  updateConfiguracoes: async (empresaId, configuracoes) => {
    try {
      const response = await apiClient.put(
        `/api/v1/empresas/${empresaId}/configuracoes`,
        configuracoes,
        {
          headers: getEmpresaHeaders(),
        }
      );
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Obter usuários da empresa
  getUsuarios: async (empresaId) => {
    try {
      const response = await apiClient.get(`/api/v1/empresas/${empresaId}/usuarios`, {
        headers: getEmpresaHeaders(),
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

  // Adicionar usuário à empresa
  addUsuario: async (empresaId, usuarioData) => {
    try {
      const response = await apiClient.post(
        `/api/v1/empresas/${empresaId}/usuarios`,
        {
          user_id: usuarioData.userId,
          papel: usuarioData.papel,
          permissoes: usuarioData.permissoes,
        },
        {
          headers: getEmpresaHeaders(),
        }
      );
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Atualizar permissões do usuário na empresa
  updateUsuarioPermissions: async (empresaId, userId, permissoes) => {
    try {
      const response = await apiClient.put(
        `/api/v1/empresas/${empresaId}/usuarios/${userId}`,
        { permissoes },
        {
          headers: getEmpresaHeaders(),
        }
      );
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },

  // Remover usuário da empresa
  removeUsuario: async (empresaId, userId) => {
    try {
      const response = await apiClient.delete(
        `/api/v1/empresas/${empresaId}/usuarios/${userId}`,
        {
          headers: getEmpresaHeaders(),
        }
      );
      
      return validateResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.message,
        error: error.code,
      };
    }
  },
};
