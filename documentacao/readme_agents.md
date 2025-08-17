## Guia dos Agentes, Dados e Orquestração

Este documento descreve, para cada agente do sistema, os objetivos, como alcançam esses objetivos, quais dados utilizam, como acessam esses dados, a origem dos dados, uso de metadados, qual banco vetorial é utilizado e como cada agente usa o mapeamento estruturado `ncm_mapping.json`.

### Visão rápida dos componentes compartilhados

- Configurações: `src/config.py` expõe caminhos e parâmetros (ex.: `NCM_MAPPING_FILE`, `FAISS_INDEX_FILE`, dimensão dos embeddings).
- Base estruturada: `data/knowledge_base/ncm_mapping.json` (gerado por `scripts/build_knowledge_base.py`).
- Banco vetorial: `FaissMetadataStore` (FAISS + SQLite) em `src/vectorstore/faiss_store.py` com embeddings 384-dim.
- Metadados por chunk (buscar): `source`, `produto_id`, `codigo_produto`, `codigo_barra`, `ncm`, `cest`, além de `chunk_id`, `start_pos`, `end_pos` (ver `src/ingestion/chunker.py`).
- Orquestração: `HybridRouter` em `src/orchestrator/hybrid_router.py` monta o contexto para os agentes:
	- Contexto estruturado: extraído de `ncm_mapping.json`.
	- Contexto semântico: resultados do FAISS (`FaissMetadataStore.search`).

---

## ExpansionAgent (src/agents/expansion_agent.py)

- Objetivo: Enriquecer descrições de produtos com informações técnicas relevantes para a classificação fiscal.
- Como alcança: Prompt para LLM (Ollama) que retorna JSON com chaves padronizadas; possui normalização de chaves e fallback de parsing.
- Dados que usa: Apenas a descrição original do produto (string).
- Como acessa: Recebe a descrição via chamada do orquestrador; chama `OllamaClient.generate()`.
- Origem dos dados: Produtos carregados do banco (via `DataLoader`) ou arquivos de entrada; não lê arquivos raw diretamente.
- Metadados: Não utiliza metadados externos; gera um trace via `BaseAgent._create_trace`.
- Banco vetorial: Não consulta FAISS diretamente.
- Uso de dados raw: Nenhum direto.
- Uso de ncm_mapping: Não utiliza diretamente.

## AggregationAgent (src/agents/aggregation_agent.py)

- Objetivo: Agrupar produtos expandidos semelhantes para reduzir processamento, elegendo representantes.
- Como alcança: TF-IDF dos textos (categoria+material+descrição+palavras-chave) + K-Means; representante é o mais próximo do centróide; fallback cria grupos individuais.
- Dados que usa: Lista de objetos gerados pelo ExpansionAgent.
- Como acessa: Recebe em memória do orquestrador; não acessa serviços externos.
- Origem dos dados: Saída do ExpansionAgent.
- Metadados: Retorna, por grupo, `grupo_id`, `representante_idx`, `membros`, `tamanho`, e `representante_produto`; gera trace.
- Banco vetorial: Não consulta FAISS.
- Uso de dados raw: Nenhum direto.
- Uso de ncm_mapping: Não utiliza.

## NCMAgent (src/agents/ncm_agent.py)

- Objetivo: Determinar o código NCM (8 dígitos) do produto.
- Como alcança: LLM com prompt que incorpora dois contextos: estruturado (oficial) e semântico (exemplos similares do FAISS). Retorna JSON com `ncm_recomendado`, confiança, justificativa, alternativos e fatores decisivos.
- Dados que usa:
	- Produto expandido (do ExpansionAgent).
	- Contexto estruturado (string gerada pelo orquestrador a partir de `ncm_mapping.json`).
	- Contexto semântico (lista de resultados do FAISS com `text`, `metadata`, `score`).
- Como acessa:
	- O orquestrador chama `HybridRouter._get_structured_context(ncm_candidate)` e injeta em `context['structured_context']`.
	- O orquestrador chama `FaissMetadataStore.search(produto_text, k=5)` e injeta em `context['semantic_context']`.
- Origem dos dados:
	- `ncm_mapping.json`: gerado por `scripts/build_knowledge_base.py` a partir de `data/raw/descricoes_ncm.json` e planilhas CEST (com herança entre NCMs quando aplicável).
	- FAISS/SQLite: construído pela ingestão (`src/main.py ingest`) a partir dos produtos do banco (via `DataLoader`) e dos chunks do `TextChunker`.
- Metadados: Usa campos de metadados do FAISS (ex.: `ncm`, `cest`, `produto_id`) para exibir exemplos semelhantes no prompt.
- Banco vetorial: `FaissMetadataStore` (FAISS IndexFlatIP + embeddings 384-dim) via orquestrador.
- Uso de dados raw: Indireto (através do `ncm_mapping.json`).
- Uso de ncm_mapping: Essencial; o contexto estruturado inclui descrição oficial, CESTs associados e exemplos; guia a decisão do LLM e valida existência/hierarquia do NCM.

## CESTAgent (src/agents/cest_agent.py)

- Objetivo: Determinar o CEST aplicável ao produto classificado em NCM.
- Como alcança: LLM com prompt incluindo o produto expandido, o NCM recomendado pelo NCMAgent e o contexto estruturado com CESTs disponíveis para aquele NCM.
- Dados que usa:
	- Produto expandido (ExpansionAgent).
	- Resultado NCM do NCMAgent.
	- Contexto estruturado com os CESTs candidatos (do `ncm_mapping.json`).
- Como acessa: Recebe `context['structured_context']` do orquestrador (que monta a partir do `ncm_mapping.json`).
- Origem dos dados: `ncm_mapping.json` unifica mapeamentos CEST (de `data/raw/CEST_RO.xlsx` e anexos) com herança onde cabível.
- Metadados: Não usa metadados do FAISS; gera trace.
- Banco vetorial: Não consulta FAISS diretamente.
- Uso de dados raw: Indireto via `ncm_mapping.json`.
- Uso de ncm_mapping: Central para listar CESTs associados ao NCM e embasar a escolha do LLM.

## ReconcilerAgent (src/agents/reconciler_agent.py)

- Objetivo: Auditar e reconciliar resultados de NCM e CEST, consolidando uma classificação final com confiança e auditoria.
- Como alcança: LLM com os resultados do NCM e CEST, mais contexto estruturado; aplica regras de consistência e produz auditoria (`consistente`, `conflitos_identificados`, `ajustes_realizados`, `alertas`).
- Dados que usa:
	- Produto expandido.
	- Resultado do NCMAgent e do CESTAgent.
	- Contexto estruturado (do `ncm_mapping.json`).
- Como acessa: Recebe tudo via `context` do orquestrador.
- Origem dos dados: `ncm_mapping.json` para validar compatibilidade NCM↔CEST.
- Metadados: Não usa metadados do FAISS; gera trace.
- Banco vetorial: Não consulta FAISS diretamente.
- Uso de dados raw: Indireto via `ncm_mapping.json`.
- Uso de ncm_mapping: Valida se o CEST proposto pertence ao NCM classificado e ajuda a justificar a decisão final.

---

## Fluxo de acesso a dados e contextos

1. Ingestão: `DataLoader` lê produtos do PostgreSQL; `TextChunker` cria chunks com metadados; `FaissMetadataStore` armazena embeddings e metadados (SQLite).
2. Classificação:
	 - ExpansionAgent enriquece a descrição (sem FAISS, sem mapping).
	 - AggregationAgent agrupa e escolhe representantes.
	 - HybridRouter gera contextos para representantes:
		 - Estruturado: leitura do `ncm_mapping.json` (via `_load_mapping_db` + `_get_structured_context`).
		 - Semântico: `vector_store.search()` em FAISS usando texto expandido + palavras-chave.
	 - NCMAgent usa ambos contextos para recomendar NCM.
	 - CESTAgent usa o NCM e o contexto estruturado para recomendar CEST.
	 - ReconcilerAgent consolida e audita NCM/CEST.
	 - Resultados dos representantes são propagados aos membros do grupo.

## Origem dos dados

- Raw (data/raw/):
	- `descricoes_ncm.json` (hierarquia NCM e descrições oficiais)
	- `CEST_RO.xlsx` e anexos (CEST oficiais)
	- `Tabela_ABC_Farma_GTIN_modificado.xlsx` (base de produtos)
	- `produtos_selecionados.json` (exemplos)
- Conhecimento estruturado: `scripts/build_knowledge_base.py` consolida os raw em `data/knowledge_base/ncm_mapping.json` (com herança CEST quando aplicável).
- Banco vetorial: gerado a partir do banco PostgreSQL (tabela `produto`) durante ingestão, com metadados por chunk.

## Resumo: uso do ncm_mapping por agente

- ExpansionAgent: não usa.
- AggregationAgent: não usa.
- NCMAgent: usa no contexto estruturado (descrições, CESTs associados, exemplos) para guiar a decisão e validar existência/hierarquia do NCM.
- CESTAgent: usa para listar e selecionar CESTs aplicáveis ao NCM classificado.
- ReconcilerAgent: usa para checar consistência NCM↔CEST e justificar a consolidação final.

