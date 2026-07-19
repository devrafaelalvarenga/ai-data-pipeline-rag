# Changelog — Document Intelligence Pipeline (RAG)

Todas as mudanças relevantes do projeto são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [0.7.0] — 19/07/2026

### Added
- `src/chunking/markdown_chunker.py` — chunking da documentação baixada em Fase 1:
  - `parse_frontmatter`: extrai `title`/`description`/`id` do frontmatter YAML
  - `split_prose_and_code`: separa prose de blocos de código (```` ``` ````) antes de fatiar, para não misturar semânticas diferentes no mesmo chunk
  - `chunk_prose`: agrupa parágrafos até `MAX_PROSE_CHARS` (1000 chars), com overlap de `PROSE_OVERLAP_CHARS` (150 chars); parágrafo maior que o limite é hard-split via sliding window
  - `chunk_code`: mantém bloco de código inteiro até `MAX_CODE_CHARS` (1000 chars); acima disso, divide por linha (nunca no meio de uma linha), com overlap de `CODE_OVERLAP_LINES` (2 linhas)
  - `chunk_document` / `chunk_all`: orquestram o chunking por arquivo e por diretório, atribuindo metadata (`source_file`, `doc_title`, `chunk_type`, `chunk_index`, `language`)
- `tests/chunking/test_markdown_chunker.py` — 20 testes unitários cobrindo frontmatter, separação prose/código, limites de tamanho, overlap e integração via `chunk_document`/`chunk_all`
- Validação manual contra o corpus real (`data/raw/dbt_docs/`): 2850 chunks gerados, 0 vazios, nenhum excedendo o tamanho máximo configurado

### Updated
- `docs/architecture.md` — seção de decisões de chunking detalhada com os parâmetros e a justificativa de medir tamanho em caracteres (não tokens, já que o modelo de embeddings ainda não foi escolhido)
- `docs/roadmap.md` — Fase 2 concluída integralmente (todas as tarefas ✅)

### Decisões técnicas
- Tamanho de chunk medido em caracteres, não tokens: o modelo de embeddings é decisão da Fase 3; caracteres são uma proxy simples e determinística até lá. Reavaliar para um budget de tokens quando o modelo for escolhido.
- Prose e código nunca compartilham chunk — mistura degrada a qualidade do embedding (ver `docs/architecture.md`).

---

## [0.6.0] — 05/07/2026

### Added
- `tests/ingestion/test_dbt_docs_ingestion.py` — 17 testes unitários cobrindo:
  - `_request_headers`: com e sem token
  - `list_markdown_files`: caminho feliz, filtro de extensão/tipo, rate limit, erros HTTP
  - `download_file`: criação de diretório, escrita de arquivo, idempotência, erro HTTP
  - `ingest_section`: orquestração, normalização de nome de pasta, seção vazia
  - `run_ingestion`: chamada por seção, estrutura do retorno
- pytest adicionado como dependência de desenvolvimento

### Updated
- `docs/roadmap.md` — Fase 1 concluída integralmente (todas as tarefas ✅)

---

## [0.5.0] — 05/07/2026

### Added
- `src/ingestion/dbt_docs_ingestion.py` — script de ingestão via API do GitHub
  - Baixa arquivos `.md` de seções configuradas (`data_modeling`, `testing`)
  - Idempotente: re-executar sobrescreve sem duplicar
  - Rate limit handling com exceção customizada `RateLimitExceeded`
  - Token lido de `.env` via `os.getenv("GITHUB_TOKEN")`
- `data/raw/dbt_docs/` — arquivos `.md` baixados das seções `data_modeling` e `testing` (~60 arquivos cada)
- `data/` adicionado ao `.gitignore` (dados brutos não vão pro git)
- `uv.lock` gerado após instalação de `requests` e `logging`

### Updated
- `pyproject.toml` — dependências: `requests>=2.34.2`, `logging>=0.4.9.6`
- `docs/roadmap.md` — Fase 1: ingestão e idempotência marcadas como concluídas

---

## [0.4.0] — 04/07/2026

### Added
- `uv` instalado (v0.11.26) via instalador oficial
- `pyproject.toml` com Python 3.12, configuração de ruff e pytest
- `.env` com estrutura completa de variáveis comentadas (GitHub, Embeddings, LLM, Chroma, Airflow)

### Updated
- `docs/roadmap.md` — Fase 0 concluída integralmente

---

## [0.3.0] — 04/07/2026

### Added
- Ambiente local Airflow inicializado via `astro dev init`
- `Dockerfile`, `airflow_settings.yaml`, `packages.txt`, `.dockerignore`
- DAG de exemplo (`dags/exampledag.py`) e teste de integridade (`tests/dags/test_dag_example.py`)
- `.astro/` com configuração interna do Astro CLI
- Ambiente validado com `astro dev start` (Airflow UI em http://ai-data-pipeline-rag.localhost:6563)

### Updated
- `docs/roadmap.md` — Fase 0: `astro dev init` e `.gitignore` marcados como concluídos

---

## [0.2.0] — 04/07/2026

### Added
- Estrutura de pastas do projeto: `dags/`, `src/` (ingestion, chunking, embeddings, quality_checks, retrieval), `notebooks/`, `tests/`, `docs/`
- `docs/integration/` com `README.md` (índice de integrações)
- `.gitignore` cobrindo `.DS_Store`, `__pycache__`, `.env`, `venv/`
- `requirements.txt` (vazio, a ser preenchido por fase)

### Updated
- `docs/architecture.md` — conteúdo completo: stack, fluxo de dados, decisões e trade-offs
- `docs/roadmap.md` — tarefas organizadas por fase (Fase 0 a 8)
- `docs/changes.md` — este arquivo, agora referenciando o projeto correto

---

## [0.1.0] — 03/07/2026

### Added
- Repositório criado: `ai-data-pipeline-rag`
- `docs/CLAUDE.md` — ponto de entrada da IA, índice de documentos, stack, regras obrigatórias
- `docs/architecture.md`, `docs/roadmap.md`, `docs/changes.md` (esqueletos iniciais)
- `README.md` inicial
