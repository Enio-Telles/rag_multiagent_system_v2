# 📊 RELATÓRIO DE QUALIDADE DO CÓDIGO
============================================================

## 📈 RESUMO EXECUTIVO
- **Total de arquivos analisados**: 29
- **Arquivos com problemas**: 29
- **Total de problemas encontrados**: 207

## 📊 PROBLEMAS POR CATEGORIA
- **Documentação**: 81
- **Formatação**: 66
- **Marcadores de código**: 40
- **Complexidade**: 17
- **Imports**: 2
- **Outros**: 1

## 📁 DETALHES POR ARQUIVO

### 📄 src\agents\aggregation_agent.py
**16 problema(s) encontrado(s):**
- Linha 161: TODO encontrado - "metodos_utilizados": ["product_deduplication_validator"] if self.enable_deduplication else ["fallback"],
- Linha 187: TODO encontrado - "metodos_utilizados": ["fallback_erro"]
- Linha 194: TODO encontrado - # Calcular confiança média entre todos os pares
- Linha 244: TODO encontrado - resultado_agrupamento: Resultado do método run()
- Linha 111: Linha muito longa (121 caracteres) - máximo 120
- Linha 127: Linha muito longa (132 caracteres) - máximo 120
- Linha 156: Linha muito longa (128 caracteres) - máximo 120
- Linha 161: Linha muito longa (121 caracteres) - máximo 120
- Linha 281: Linha muito longa (126 caracteres) - máximo 120
- Linha 15: Import muito longo - considere quebrar em múltiplas linhas
- Linha 46: Função '__init__' sem docstring
- Linha 18: Classe 'ProductDeduplicationValidator' sem docstring
- Linha 26: Função 'validate_product_deduplication' sem docstring
- Linha 19: Função 'group_identical_products' sem docstring
- Linha 21: Função 'products_are_identical' sem docstring
- Linha 23: Função 'suggest_canonical_description' sem docstring

### 📄 src\agents\aggregation_agent_new.py
**16 problema(s) encontrado(s):**
- Linha 155: TODO encontrado - "metodos_utilizados": ["product_deduplication_validator"] if self.enable_deduplication else ["fallback"],
- Linha 181: TODO encontrado - "metodos_utilizados": ["fallback_erro"]
- Linha 188: TODO encontrado - # Calcular confiança média entre todos os pares
- Linha 238: TODO encontrado - resultado_agrupamento: Resultado do método run()
- Linha 105: Linha muito longa (121 caracteres) - máximo 120
- Linha 121: Linha muito longa (132 caracteres) - máximo 120
- Linha 150: Linha muito longa (128 caracteres) - máximo 120
- Linha 155: Linha muito longa (121 caracteres) - máximo 120
- Linha 275: Linha muito longa (126 caracteres) - máximo 120
- Linha 14: Import muito longo - considere quebrar em múltiplas linhas
- Linha 45: Função '__init__' sem docstring
- Linha 17: Classe 'ProductDeduplicationValidator' sem docstring
- Linha 25: Função 'validate_product_deduplication' sem docstring
- Linha 18: Função 'group_identical_products' sem docstring
- Linha 20: Função 'products_are_identical' sem docstring
- Linha 22: Função 'suggest_canonical_description' sem docstring

### 📄 src\agents\base_agent.py
**4 problema(s) encontrado(s):**
- Linha 13: TODO encontrado - """Classe base para todos os agentes do sistema."""
- Linha 95: TODO encontrado - """Método principal que cada agente deve implementar."""
- Linha 190: Linha muito longa (122 caracteres) - máximo 120
- Linha 15: Função '__init__' sem docstring

### 📄 src\agents\cest_agent.py
**11 problema(s) encontrado(s):**
- Linha 24: TODO encontrado - 2. Nem todos os NCMs possuem CEST correspondente
- Linha 34: XXX encontrado - - NÃO confundir com NCM que tem formato XXXX.XX.XX
- Linha 39: XXX encontrado - - NCM 3004.xx.xx (medicamentos): SEMPRE usar CESTs da categoria 13.xxx.xx
- Linha 269: TODO encontrado - # Deve ser todos dígitos
- Linha 18: Linha muito longa (127 caracteres) - máximo 120
- Linha 109: Linha muito longa (122 caracteres) - máximo 120
- Linha 132: Linha muito longa (122 caracteres) - máximo 120
- Linha 143: Linha muito longa (146 caracteres) - máximo 120
- Linha 170: Linha muito longa (128 caracteres) - máximo 120
- Linha 15: Função '__init__' sem docstring
- Linha 67: Função 'run' muito complexa (complexidade: 19)

### 📄 src\agents\cest_agent_new.py
**7 problema(s) encontrado(s):**
- Linha 24: TODO encontrado - 2. Nem todos os NCMs possuem CEST correspondente
- Linha 18: Linha muito longa (127 caracteres) - máximo 120
- Linha 52: Linha muito longa (122 caracteres) - máximo 120
- Linha 75: Linha muito longa (122 caracteres) - máximo 120
- Linha 87: Linha muito longa (127 caracteres) - máximo 120
- Linha 105: Linha muito longa (127 caracteres) - máximo 120
- Linha 15: Função '__init__' sem docstring

### 📄 src\agents\expansion_agent.py
**3 problema(s) encontrado(s):**
- Linha 24: Linha muito longa (133 caracteres) - máximo 120
- Linha 16: Função '__init__' sem docstring
- Linha 45: Função 'run' muito complexa (complexidade: 13)

### 📄 src\agents\ncm_agent.py
**8 problema(s) encontrado(s):**
- Linha 25: Linha muito longa (156 caracteres) - máximo 120
- Linha 26: Linha muito longa (247 caracteres) - máximo 120
- Linha 63: Linha muito longa (122 caracteres) - máximo 120
- Linha 89: Linha muito longa (123 caracteres) - máximo 120
- Linha 129: Linha muito longa (124 caracteres) - máximo 120
- Linha 140: Linha muito longa (148 caracteres) - máximo 120
- Linha 15: Função '__init__' sem docstring
- Linha 48: Função 'run' muito complexa (complexidade: 20)

### 📄 src\agents\reconciler_agent.py
**9 problema(s) encontrado(s):**
- Linha 18: Linha muito longa (128 caracteres) - máximo 120
- Linha 47: Linha muito longa (136 caracteres) - máximo 120
- Linha 71: Linha muito longa (122 caracteres) - máximo 120
- Linha 88: Linha muito longa (123 caracteres) - máximo 120
- Linha 106: Linha muito longa (129 caracteres) - máximo 120
- Linha 121: Linha muito longa (153 caracteres) - máximo 120
- Linha 158: Linha muito longa (132 caracteres) - máximo 120
- Linha 183: Linha muito longa (132 caracteres) - máximo 120
- Linha 15: Função '__init__' sem docstring

### 📄 src\api\review_api.py
**11 problema(s) encontrado(s):**
- Linha 201: TODO encontrado - """Retorna todos os detalhes de uma classificação específica"""
- Linha 330: TODO encontrado - confirmar: bool = Query(False, description="Confirmação obrigatória para limpar todo o Golden Set"),
- Linha 333: TODO encontrado - """Limpa todo o Golden Set (marca todas as entradas como inativas)"""
- Linha 622: XXX encontrado - "estrutura": "Segmento.Item.SubItem (XX.XXX.XX)",
- Linha 65: Classe 'ClassificacaoResponse' sem docstring
- Linha 79: Classe 'ClassificacaoDetalhe' sem docstring
- Linha 102: Classe 'RevisaoRequest' sem docstring
- Linha 114: Classe 'GoldenSetRequest' sem docstring
- Linha 119: Classe 'CodigoBarraValidacao' sem docstring
- Linha 125: Classe 'DashboardStats' sem docstring
- Linha 400: Classe 'ClassificarComExplicacaoRequest' sem docstring

### 📄 src\api\review_api_backup.py
**13 problema(s) encontrado(s):**
- Linha 230: TODO encontrado - Retorna todos os detalhes de uma classificação específica
- Linha 536: XXX encontrado - # NCM: 8 dígitos, CEST: formato XX.XXX.XX
- Linha 605: TODO encontrado - Retorna todos os detalhes de uma classificação específica
- Linha 958: TODO encontrado - Retorna todos os detalhes de uma classificação específica
- Linha 1344: TODO encontrado - Retorna todos os detalhes de uma classificação específica
- Linha 89: Classe 'ClassificacaoResponse' sem docstring
- Linha 103: Classe 'ClassificacaoDetalhe' sem docstring
- Linha 126: Classe 'RevisaoRequest' sem docstring
- Linha 138: Classe 'CodigoBarraValidacao' sem docstring
- Linha 144: Classe 'DashboardStats' sem docstring
- Linha 154: Classe 'LoginRequest' sem docstring
- Linha 515: Classe 'UserResponse' sem docstring
- Linha 159: Função 'validate_email' sem docstring

### 📄 src\api\review_api_secure.py
**15 problema(s) encontrado(s):**
- Linha 150: XXX encontrado - raise ValueError('CEST deve ter formato XX.XXX.XX')
- Linha 200: XXX encontrado - # NCM: 8 dígitos, CEST: formato XX.XXX.XX
- Linha 345: TODO encontrado - Retorna todos os detalhes de uma classificação específica
- Linha 65: Linha muito longa (131 caracteres) - máximo 120
- Linha 86: Classe 'ClassificacaoResponse' sem docstring
- Linha 100: Classe 'ClassificacaoDetalhe' sem docstring
- Linha 123: Classe 'RevisaoRequest' sem docstring
- Linha 153: Classe 'CodigoBarraValidacao' sem docstring
- Linha 159: Classe 'DashboardStats' sem docstring
- Linha 169: Classe 'LoginRequest' sem docstring
- Linha 179: Classe 'UserResponse' sem docstring
- Linha 136: Função 'validate_acao' sem docstring
- Linha 142: Função 'validate_ncm' sem docstring
- Linha 148: Função 'validate_cest' sem docstring
- Linha 174: Função 'validate_email' sem docstring

### 📄 src\config.py
**1 problema(s) encontrado(s):**
- Linha 8: Classe 'Config' sem docstring

### 📄 src\config\settings.py
**1 problema(s) encontrado(s):**
- Linha 119: Função '__init__' sem docstring

### 📄 src\database\models.py
**6 problema(s) encontrado(s):**
- Linha 34: Linha muito longa (135 caracteres) - máximo 120
- Linha 82: Função '__repr__' sem docstring
- Linha 97: Função '__repr__' sem docstring
- Linha 137: Função '__repr__' sem docstring
- Linha 194: Função '__repr__' sem docstring
- Linha 251: Função '__repr__' sem docstring

### 📄 src\domain\product_compatibility.py
**4 problema(s) encontrado(s):**
- Linha 210: Linha muito longa (162 caracteres) - máximo 120
- Linha 41: Função '__init__' sem docstring
- Linha 18: Classe 'NcmFormatValidator' sem docstring
- Linha 20: Função 'get_hierarchy_info' sem docstring

### 📄 src\domain\product_deduplication.py
**7 problema(s) encontrado(s):**
- Linha 279: Linha muito longa (121 caracteres) - máximo 120
- Linha 281: Linha muito longa (122 caracteres) - máximo 120
- Linha 303: Linha muito longa (125 caracteres) - máximo 120
- Linha 364: Linha muito longa (129 caracteres) - máximo 120
- Linha 26: Função '__init__' sem docstring
- Linha 254: Função 'products_are_identical' muito complexa (complexidade: 12)
- Linha 322: Função '_calculate_similarity_flexible' muito complexa (complexidade: 15)

### 📄 src\domain\validators.py
**6 problema(s) encontrado(s):**
- Linha 310: Linha muito longa (127 caracteres) - máximo 120
- Linha 343: Linha muito longa (130 caracteres) - máximo 120
- Linha 28: Função 'is_valid' sem docstring
- Linha 41: Função 'is_valid' sem docstring
- Linha 180: Função '__init__' sem docstring
- Linha 244: Função '__init__' sem docstring

### 📄 src\feedback\consulta_metadados_service.py
**3 problema(s) encontrado(s):**
- Linha 99: Linha muito longa (135 caracteres) - máximo 120
- Linha 262: Linha muito longa (126 caracteres) - máximo 120
- Linha 21: Função '__init__' sem docstring

### 📄 src\feedback\continuous_learning.py
**8 problema(s) encontrado(s):**
- Linha 46: Função '__init__' sem docstring
- Linha 197: Função '__init__' sem docstring
- Linha 312: Função '__init__' sem docstring
- Linha 31: Classe 'SentenceTransformer' sem docstring
- Linha 35: Classe 'Config' sem docstring
- Linha 32: Função '__init__' sem docstring
- Linha 33: Função 'encode' sem docstring
- Linha 36: Função '__init__' sem docstring

### 📄 src\feedback\explicacao_service.py
**3 problema(s) encontrado(s):**
- Linha 65: TODO encontrado - Método alternativo para compatibilidade com HybridRouter
- Linha 72: Linha muito longa (123 caracteres) - máximo 120
- Linha 18: Função 'clean_circular_references' muito complexa (complexidade: 12)

### 📄 src\feedback\explicacao_service_broken.py
**2 problema(s) encontrado(s):**
- Linha 68: Linha muito longa (121 caracteres) - máximo 120
- Erro de sintaxe: unexpected indent (<unknown>, line 65)

### 📄 src\feedback\review_service.py
**14 problema(s) encontrado(s):**
- Linha 113: TODO encontrado - # Buscar todos os produtos pendentes
- Linha 211: TODO encontrado - Retorna todos os detalhes de uma classificação específica
- Linha 1001: TODO encontrado - Limpa todo o Golden Set (marca todas as entradas como inativas)
- Linha 178: Linha muito longa (134 caracteres) - máximo 120
- Linha 483: Linha muito longa (157 caracteres) - máximo 120
- Linha 825: Linha muito longa (130 caracteres) - máximo 120
- Linha 827: Linha muito longa (132 caracteres) - máximo 120
- Linha 840: Linha muito longa (185 caracteres) - máximo 120
- Linha 844: Linha muito longa (124 caracteres) - máximo 120
- Linha 29: Função '__init__' sem docstring
- Linha 77: Função 'obter_proximo_pendente' muito complexa (complexidade: 18)
- Linha 244: Função 'processar_revisao' muito complexa (complexidade: 14)
- Linha 453: Função 'adicionar_ao_golden_set' muito complexa (complexidade: 12)
- Linha 793: Função '_extrair_justificativa_completa' muito complexa (complexidade: 20)

### 📄 src\ingestion\chunker.py
**2 problema(s) encontrado(s):**
- Linha 8: Classe 'TextChunker' sem docstring
- Linha 9: Função '__init__' sem docstring

### 📄 src\ingestion\data_loader.py
**5 problema(s) encontrado(s):**
- Linha 222: TODO encontrado - # Combinar todos os DataFrames
- Linha 33: Linha muito longa (210 caracteres) - máximo 120
- Linha 12: Classe 'DataLoader' sem docstring
- Linha 13: Função '__init__' sem docstring
- Linha 157: Função 'load_cest_mapping' muito complexa (complexidade: 17)

### 📄 src\llm\ollama_client.py
**2 problema(s) encontrado(s):**
- Linha 9: Classe 'OllamaClient' sem docstring
- Linha 10: Função '__init__' sem docstring

### 📄 src\main.py
**8 problema(s) encontrado(s):**
- Linha 363: TODO encontrado - print("   Isso irá apagar todos os dados existentes!")
- Linha 518: TODO encontrado - print("\n🎉 TODOS OS TESTES DAS FASES 4 E 5 PASSARAM!")
- Linha 90: Linha muito longa (121 caracteres) - máximo 120
- Linha 150: Linha muito longa (122 caracteres) - máximo 120
- Linha 347: Linha muito longa (129 caracteres) - máximo 120
- Linha 123: Função 'get_confianca_float' sem docstring
- Linha 332: Função 'command_setup_review' muito complexa (complexidade: 14)
- Linha 528: Função 'main' muito complexa (complexidade: 11)

### 📄 src\orchestrator\hybrid_router.py
**18 problema(s) encontrado(s):**
- Linha 52: TODO encontrado - Orquestrador principal que coordena todo o fluxo de trabalho do sistema agêntico híbrido.
- Linha 342: XXX encontrado - - Para medicamentos, usar sempre CESTs da categoria 13.xxx.xx""")
- Linha 354: XXX encontrado - - Para CEST, usar sempre o Segmento 13 (13.xxx.xx) para medicamentos""")
- Linha 551: TODO encontrado - # Criar produto expandido mantendo todos os campos originais + dados de expansão
- Linha 650: TODO encontrado - print("📤 Etapa 4: Propagando resultados para todos os produtos...")
- Linha 733: TODO encontrado - # Configurar rastreamento de consultas em todos os agentes
- Linha 315: Linha muito longa (122 caracteres) - máximo 120
- Linha 325: Linha muito longa (128 caracteres) - máximo 120
- Linha 349: Linha muito longa (152 caracteres) - máximo 120
- Linha 568: Linha muito longa (121 caracteres) - máximo 120
- Linha 713: Linha muito longa (125 caracteres) - máximo 120
- Linha 771: Linha muito longa (121 caracteres) - máximo 120
- Linha 855: Linha muito longa (126 caracteres) - máximo 120
- Linha 59: Função '__init__' sem docstring
- Linha 297: Função '_get_structured_context' muito complexa (complexidade: 17)
- Linha 361: Função '_get_semantic_context' muito complexa (complexidade: 15)
- Linha 524: Função 'classify_products' muito complexa (complexidade: 15)
- Linha 713: Função 'classify_product_with_explanations' muito complexa (complexidade: 14)

### 📄 src\vectorstore\embedder.py
**2 problema(s) encontrado(s):**
- Linha 9: Classe 'Embedder' sem docstring
- Linha 10: Função '__init__' sem docstring

### 📄 src\vectorstore\faiss_store.py
**2 problema(s) encontrado(s):**
- Linha 12: Classe 'FaissMetadataStore' sem docstring
- Linha 13: Função '__init__' sem docstring

## 💡 RECOMENDAÇÕES
- **TODOs/FIXMEs**: Revisar e implementar ou remover marcadores antigos
- **Documentação**: Adicionar docstrings em funções e classes públicas
- **Formatação**: Considerar usar ferramentas como `black` para formatação automática
- **Complexidade**: Refatorar funções complexas em funções menores
- **Imports**: Organizar e otimizar imports usando ferramentas como `isort`