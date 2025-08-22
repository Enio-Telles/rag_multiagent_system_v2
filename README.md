# Sistema RAG Multiagente para Classificação Fiscal (NCM/CEST)

Este é um sistema avançado de classificação fiscal automatizada que utiliza uma arquitetura de Inteligência Artificial com múltiplos agentes para determinar códigos **NCM (Nomenclatura Comum do Mercosul)** e **CEST (Código Especificador da Substituição Tributária)** para produtos comerciais.

O projeto combina um sistema RAG (Retrieval Augmented Generation) híbrido com agentes de IA especializados para oferecer classificações rápidas, precisas e auditáveis, adaptando-se ao contexto específico de cada empresa.

## ✨ Principais Características

- **🤖 5 Agentes de IA Especializados**: O sistema utiliza cinco agentes distintos (Expansão, Agregação, NCM, CEST e Reconciliação) que trabalham em conjunto para analisar, enriquecer e classificar os produtos.
- **🧠 Sistema RAG Híbrido**: Combina busca em conhecimento estruturado (banco de dados relacional) e não estruturado (busca vetorial com FAISS) para máxima precisão.
- **⚡ Performance Otimizada**: Com um banco de dados SQLite unificado, o sistema atinge tempos de resposta de ~5ms por consulta, uma melhoria de 98% em relação a abordagens tradicionais.
- **🏢 Contexto Empresarial**: As classificações são adaptadas às regras de negócio e ao ramo de atividade da empresa, garantindo conformidade tributária.
- **🌐 Interface Web e API REST**: Inclui uma interface web completa para revisão humana das classificações e uma API REST para integração com outros sistemas.
- **🔍 Rastreabilidade e Auditoria**: Todas as decisões tomadas pelos agentes são completamente rastreáveis, fornecendo uma trilha de auditoria detalhada.

## 🏗️ Arquitetura do Sistema

O sistema é organizado em uma arquitetura de quatro camadas, garantindo modularidade e escalabilidade.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                      │
├─────────────────────────────────────────────────────────────────┤
│  🌐 Interface Web     │  📱 API REST     │  🔧 CLI Tools      │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE ORQUESTRAÇÃO                      │
├─────────────────────────────────────────────────────────────────┤
│              🎛️ HybridRouter (Orquestrador Principal)           │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE AGENTES IA                        │
├─────────────────────────────────────────────────────────────────┤
│ 🔍 Expansion │ 🎲 Aggregation │ 🧠 NCM │ 🎯 CEST │ ⚖️ Reconciler │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE CONHECIMENTO                      │
├─────────────────────────────────────────────────────────────────┤
│  📚 RAG/FAISS  │  🗄️ SQLite    │  🐘 PostgreSQL │  🏆 Golden Set │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.8+, FastAPI, Uvicorn, Pandas
- **IA & Machine Learning**: Ollama (para LLMs), Sentence-Transformers, Faiss, Scikit-learn
- **Banco de Dados**: SQLite (principal), PostgreSQL (backup/analítico)
- **Frontend**: React, Material-UI, Axios

## 📂 Estrutura do Projeto

A estrutura de diretórios foi projetada para ser intuitiva e modular:

```
├── 📁 documentos/              # Documentação detalhada do projeto
├── 📁 src/                      # Código fonte principal do backend
│   ├── 📁 agents/               # Agentes especializados de IA
│   ├── 📁 api/                  # Endpoints da API REST
│   ├── 📁 core/                 # Funcionalidades centrais do sistema
│   ├── 📁 database/             # Modelos e conexão com banco de dados
│   ├── 📁 orchestrator/         # Orquestração dos agentes
│   └── 📁 vectorstore/          # Lógica de busca vetorial (FAISS)
├── 📁 frontend/                 # Código fonte da interface web (React)
├── 📁 data/                     # Dados, incluindo o banco SQLite e índices FAISS
├── 📁 scripts/                  # Scripts utilitários (ex: build da base de conhecimento)
├── 📄 requirements.txt          # Dependências Python
└── 📄 README.md                 # Este arquivo
```

## 🚀 Começando

Siga os passos abaixo para configurar e executar o projeto localmente.

### Pré-requisitos

- Python 3.8 ou superior
- Git
- Ollama instalado e em execução.

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd <NOME_DO_DIRETORIO>
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências Python:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Baixe o modelo de linguagem (LLM):**
    Este projeto usa o `llama3.1:8b` por padrão.
    ```bash
    ollama pull llama3.1:8b
    ```

5.  **Instale as dependências do frontend:**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

### Executando o Sistema

1.  **Inicialize o banco de dados e a base de conhecimento:**
    Este comando prepara o banco de dados SQLite e os índices FAISS.
    ```bash
    python initialize_system.py
    ```

2.  **Inicie o sistema unificado (Backend + Frontend):**
    ```bash
    python start_unified_system.py
    ```

- A **API** estará disponível em `http://localhost:8000`.
- A **Interface Web** estará disponível em `http://localhost:3000`.

## ⚙️ Como Funciona

O processo de classificação de um produto segue um fluxo orquestrado:

1.  **Entrada**: Uma lista de produtos com descrições é enviada para o sistema.
2.  **Expansão (ExpansionAgent)**: A descrição de cada produto é enriquecida com detalhes técnicos e sinônimos.
3.  **Agregação (AggregationAgent)**: Produtos similares são agrupados para otimizar o processamento e garantir consistência.
4.  **Classificação NCM (NCMAgent)**: Usando os contextos estruturado (banco de dados) e semântico (RAG/FAISS), o agente recomenda o código NCM mais apropriado.
5.  **Determinação CEST (CESTAgent)**: Com base no NCM classificado, este agente determina se um código CEST é aplicável e o seleciona.
6.  **Reconciliação (ReconcilerAgent)**: O agente final valida a consistência entre NCM e CEST, calcula uma pontuação de confiança e gera uma justificativa detalhada para a classificação.
7.  **Saída**: O sistema retorna a classificação completa, incluindo NCM, CEST, confiança e trilha de auditoria.

## 📖 Índice da Documentação

A pasta `/documentos` contém manuais detalhados e relatórios sobre a implementação do sistema. Abaixo estão alguns dos documentos mais importantes:

-   **`14_MANUAL_COMPLETO_SISTEMA.md`**: O guia mais completo, detalhando toda a arquitetura, agentes, APIs e processos de configuração.
-   **`55_readme_agents.md`**: Um guia focado no desenvolvedor, explicando como cada agente acessa e utiliza os dados.
-   **`50_GUIA_INTERFACE_WEB.md`**: Um manual sobre como utilizar a interface web de revisão e auditoria.
-   **`49_GOLDEN_SET_EXPLICACAO.md`**: Explicação sobre o conceito de Golden Set e como ele é utilizado para a aprendizagem contínua do sistema.
-   **`11_INTEGRACAO_AGENTES_DETALHADA.md`**: Detalhes técnicos sobre a integração e comunicação entre os diferentes agentes de IA.

## 📚 Documentação Adicional

Para uma visão aprofundada da arquitetura, funcionamento de cada agente, esquemas de banco de dados e detalhes de implementação, consulte os manuais na pasta `/documentos`.
