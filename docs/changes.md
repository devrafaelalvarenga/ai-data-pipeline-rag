# Changelog — Document Intelligence Pipeline (RAG)

Todas as mudanças relevantes do projeto são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

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
