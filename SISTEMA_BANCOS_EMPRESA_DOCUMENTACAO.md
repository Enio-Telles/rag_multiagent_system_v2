# 🏢 Sistema de Bancos de Dados por Empresa - Documentação Completa

## 📋 **VISÃO GERAL**

Sistema avançado que cria bancos de dados SQLite separados para cada empresa, mantendo classificações, descrições enriquecidas, justificativas de agentes e histórico completo de consultas. O Golden Set permanece como referência compartilhada entre todas as empresas.

## 🏗️ **ARQUITETURA DO SISTEMA**

### **Estrutura de Bancos**
```
data/
├── empresas/
│   ├── empresa_1.db     # Banco da empresa 1
│   ├── empresa_2.db     # Banco da empresa 2
│   └── empresa_N.db     # Banco da empresa N
└── golden_set_shared.db # Golden Set compartilhado
```

### **Tabelas por Empresa**
Cada banco de empresa contém 7 tabelas principais:

#### 1️⃣ **empresa_info**
```sql
- id, nome, cnpj, tipo_atividade
- descricao_atividade, canal_venda
- porte_empresa, regime_tributario
- segmento_cest_preferencial
- data_criacao, data_atualizacao
```

#### 2️⃣ **produtos_empresa**
```sql
- id, gtin, nome_produto
- descricao_original, descricao_enriquecida
- categoria, marca, peso, unidade_medida, preco
- data_cadastro, data_atualizacao, ativo
```

#### 3️⃣ **classificacoes**
```sql
- id, produto_id, ncm_codigo, ncm_descricao
- cest_codigo, cest_descricao
- confianca_ncm, confianca_cest
- status (pendente/aprovado/rejeitado/revisao)
- aprovado_por, data_classificacao, data_aprovacao
- observacoes
```

#### 4️⃣ **agente_acoes**
```sql
- id, produto_id, classificacao_id
- agente_nome (expansion/ncm/cest/aggregation/reconciler)
- acao_tipo (busca/classificacao/validacao/correcao)
- input_dados (JSON), output_resultado (JSON)
- justificativa, confianca, tempo_execucao
- data_execucao, sucesso, erro_detalhes
```

#### 5️⃣ **agente_consultas**
```sql
- id, produto_id, agente_nome
- tipo_consulta (semantic_search/database_lookup/api_call)
- query_original, query_processada
- resultados_encontrados, resultado_detalhes (JSON)
- relevancia_score, tempo_resposta
- data_consulta, sucesso
```

#### 6️⃣ **historico_mudancas**
```sql
- id, produto_id, classificacao_id
- tipo_mudanca (criacao/atualizacao/aprovacao/rejeicao)
- campo_alterado, valor_anterior, valor_novo
- usuario, motivo, data_mudanca
```

#### 7️⃣ **metricas_performance**
```sql
- id, data_calculo
- total_produtos, total_classificacoes
- aprovacoes_automaticas, aprovacoes_manuais, rejeicoes
- tempo_medio_classificacao
- confianca_media_ncm, confianca_media_cest
- produtos_golden_set, taxa_sucesso
- dados_detalhados (JSON)
```

### **Golden Set Compartilhado**
Banco separado com tabelas:

#### **golden_set_produtos**
```sql
- id, gtin, nome_produto, descricao_padronizada
- ncm_codigo, ncm_descricao, cest_codigo, cest_descricao
- categoria_padrao, subcategoria
- confianca_validacao, origem_validacao
- numero_validacoes, data_criacao, data_atualizacao
- ativo, observacoes
```

#### **golden_set_validacoes**
```sql
- id, produto_golden_id, empresa_origem_id
- validador, tipo_validacao (manual/automatica)
- confianca, observacoes, data_validacao
```

## 🔧 **COMPONENTES IMPLEMENTADOS**

### **1. EmpresaDatabaseManager**
**Arquivo**: `src/database/empresa_database_manager.py`

Responsabilidades:
- ✅ Criar bancos SQLite por empresa
- ✅ Gerenciar estrutura de tabelas
- ✅ Inserir produtos e classificações
- ✅ Rastrear ações e consultas de agentes
- ✅ Manter Golden Set compartilhado
- ✅ Gerar estatísticas e relatórios

**Métodos principais:**
```python
create_empresa_database(empresa_id, empresa_info)
insert_produto(empresa_id, produto_data)
insert_classificacao(empresa_id, produto_id, classificacao_data)
insert_agente_acao(empresa_id, acao_data)
insert_agente_consulta(empresa_id, consulta_data)
get_empresa_stats(empresa_id)
get_produto_detalhado(empresa_id, produto_id)
```

### **2. EmpresaClassificacaoService**
**Arquivo**: `src/services/empresa_classificacao_service.py`

Responsabilidades:
- ✅ Integrar classificação com bancos segregados
- ✅ Rastrear ações dos agentes durante classificação
- ✅ Aprovar/rejeitar classificações
- ✅ Adicionar produtos ao Golden Set
- ✅ Gerar relatórios empresariais

**Métodos principais:**
```python
inicializar_empresa(empresa_data)
classificar_produto_empresa(empresa_id, produto_data, hybrid_router)
aprovar_classificacao(empresa_id, classificacao_id, usuario, observacoes)
rejeitar_classificacao(empresa_id, classificacao_id, usuario, motivo)
adicionar_ao_golden_set(empresa_id, produto_id, usuario)
get_relatorio_empresa(empresa_id)
```

### **3. API Endpoints**
**Arquivo**: `src/api/empresa_database_api.py`

**Endpoints disponíveis:**

#### **🏢 Gestão de Empresas**
- `POST /api/v1/empresa-db/inicializar` - Criar nova empresa
- `GET /api/v1/empresa-db/empresas` - Listar todas empresas
- `GET /api/v1/empresa-db/empresas/{id}/stats` - Estatísticas da empresa
- `GET /api/v1/empresa-db/empresas/{id}/relatorio` - Relatório completo

#### **📦 Gestão de Produtos**
- `POST /api/v1/empresa-db/empresas/{id}/produtos` - Classificar produto
- `GET /api/v1/empresa-db/empresas/{id}/produtos` - Listar produtos
- `GET /api/v1/empresa-db/empresas/{id}/produtos/{produto_id}` - Detalhes do produto

#### **✅ Gestão de Classificações**
- `POST /api/v1/empresa-db/empresas/{id}/classificacoes/{class_id}/aprovar` - Aprovar classificação
- `POST /api/v1/empresa-db/empresas/{id}/classificacoes/{class_id}/rejeitar` - Rejeitar classificação

#### **🏆 Golden Set**
- `POST /api/v1/empresa-db/empresas/{id}/produtos/{produto_id}/golden-set` - Adicionar ao Golden Set
- `GET /api/v1/empresa-db/golden-set` - Listar Golden Set
- `GET /api/v1/empresa-db/golden-set/{id}/validacoes` - Validações do Golden Set

#### **📊 Analytics**
- `GET /api/v1/empresa-db/empresas/{id}/agentes/performance` - Performance dos agentes

## 🚀 **COMO USAR**

### **1. Inicializar Sistema**
```bash
# Testar sistema completo
python test_sistema_bancos_empresa.py

# Integrar endpoints na API
python integrar_endpoints_banco_empresa.py
```

### **2. Criar Nova Empresa**
```bash
curl -X POST "http://localhost:8000/api/v1/empresa-db/inicializar" \
     -H "Content-Type: application/json" \
     -d '{
       "nome": "COSMÉTICOS PORTA A PORTA LTDA",
       "cnpj": "12.345.678/0001-90",
       "tipo_atividade": "Comercio varejista porta a porta",
       "descricao_atividade": "Venda de cosméticos em domicílio",
       "canal_venda": "porta_a_porta",
       "porte_empresa": "EPP",
       "regime_tributario": "SIMPLES_NACIONAL"
     }'
```

### **3. Classificar Produto**
```bash
curl -X POST "http://localhost:8000/api/v1/empresa-db/empresas/1/produtos" \
     -H "Content-Type: application/json" \
     -d '{
       "nome_produto": "Batom Vermelho Matte",
       "descricao_original": "Batom de longa duração",
       "categoria": "Cosméticos",
       "marca": "BeautyBrand",
       "preco": 29.90
     }'
```

### **4. Aprovar Classificação**
```bash
curl -X POST "http://localhost:8000/api/v1/empresa-db/empresas/1/classificacoes/1/aprovar" \
     -H "Content-Type: application/json" \
     -d '{
       "usuario": "revisor@empresa.com",
       "observacoes": "Classificação validada manualmente"
     }'
```

### **5. Obter Relatório**
```bash
curl -X GET "http://localhost:8000/api/v1/empresa-db/empresas/1/relatorio"
```

## 📊 **RASTREAMENTO DE AGENTES**

### **Ações Rastreadas**
Para cada produto classificado, o sistema registra:

- **🤖 Agente**: expansion, ncm, cest, aggregation, reconciler
- **⚡ Ação**: busca, classificacao, validacao, correcao
- **📥 Input**: Dados de entrada (JSON)
- **📤 Output**: Resultado da ação (JSON)
- **💭 Justificativa**: Explicação da decisão
- **🎯 Confiança**: Score de confiança
- **⏱️ Tempo**: Duração da execução
- **✅ Sucesso**: Status da operação

### **Consultas Rastreadas**
- **🔍 Tipo**: semantic_search, database_lookup, api_call
- **📝 Query**: Query original e processada
- **📊 Resultados**: Quantidade e detalhes encontrados
- **🎯 Relevância**: Score de relevância
- **⏱️ Tempo**: Tempo de resposta

## 🎯 **BENEFÍCIOS DO SISTEMA**

### **Segregação por Empresa**
- ✅ **Isolamento**: Dados separados por empresa
- ✅ **Performance**: Bancos menores e otimizados
- ✅ **Segurança**: Acesso controlado por empresa
- ✅ **Backup**: Backup individual por empresa

### **Rastreabilidade Completa**
- ✅ **Auditoria**: Histórico completo de mudanças
- ✅ **Debug**: Rastreamento de ações dos agentes
- ✅ **Analytics**: Métricas de performance
- ✅ **Compliance**: Justificativas para todas as decisões

### **Golden Set Centralizado**
- ✅ **Referência**: Base comum para todas empresas
- ✅ **Qualidade**: Produtos validados e aprovados
- ✅ **Aprendizado**: Melhoria contínua do sistema
- ✅ **Consenso**: Validações de múltiplas empresas

### **APIs Robustas**
- ✅ **RESTful**: Endpoints padronizados
- ✅ **Documentação**: Swagger/OpenAPI integrado
- ✅ **Validação**: Modelos Pydantic
- ✅ **Tratamento**: Erros bem estruturados

## 📈 **MÉTRICAS E RELATÓRIOS**

### **Estatísticas por Empresa**
- Total de produtos cadastrados
- Total de classificações realizadas
- Taxa de aprovação/rejeição
- Confiança média NCM/CEST
- Performance por agente
- Tempo médio de classificação

### **Relatórios Disponíveis**
- Relatório geral da empresa
- Performance dos agentes
- Histórico de classificações
- Produtos no Golden Set
- Auditoria de mudanças

## 🔮 **PRÓXIMOS PASSOS**

### **Melhorias Planejadas**
- [ ] Dashboard web para visualização
- [ ] Relatórios em PDF/Excel
- [ ] Sistema de notificações
- [ ] Backup automático dos bancos
- [ ] Sincronização entre empresas
- [ ] Machine Learning para sugestões
- [ ] API de importação/exportação
- [ ] Sistema de usuários por empresa

### **Integrações Futuras**
- [ ] ERP empresariais
- [ ] Sistemas de e-commerce
- [ ] APIs de órgãos fiscais
- [ ] Plataformas de BI
- [ ] Sistemas de auditoria

---

## 📝 **CONCLUSÃO**

O sistema de bancos de dados por empresa oferece:

✅ **Segregação completa** de dados por empresa
✅ **Rastreabilidade total** das ações dos agentes
✅ **Golden Set centralizado** para referência
✅ **APIs robustas** para integração
✅ **Relatórios detalhados** para gestão
✅ **Performance otimizada** com SQLite
✅ **Escalabilidade** para múltiplas empresas

**🚀 Sistema pronto para produção com arquitetura escalável e funcionalidades avançadas!**
