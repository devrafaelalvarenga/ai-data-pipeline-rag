# Roadmap — Document Intelligence Pipeline (RAG)

Tarefas organizadas por fase do projeto. Atualizar status sempre que uma etapa for iniciada ou concluída.

---

## Fase 0 — Setup e Estrutura

| Status | Tarefa |
|---|---|
| ✅ | Criar repositório `ai-data-pipeline-rag` no GitHub |
| ✅ | Definir estrutura de pastas do projeto |
| ✅ | Criar `docs/` com `architecture.md`, `roadmap.md`, `changes.md` |
| ✅ | Criar `docs/CLAUDE.md` como ponto de entrada da IA |
| ✅ | Inicializar ambiente com Astro CLI (`astro dev init`) |
| ✅ | Configurar `uv` e criar `pyproject.toml` |
| ✅ | Criar `.env` com estrutura de variáveis comentadas (valores em branco) |
| ✅ | Garantir que `.env` preenchido está no `.gitignore` |

---

## Fase 1 — Ingestão

| Status | Tarefa |
|---|---|
| ✅ | Implementar `src/ingestion/` — pull de Markdown da API do GitHub |
| ✅ | Garantir idempotência (não reprocessar docs que não mudaram) |
| ✅ | Cobrir com testes unitários (`tests/`) |

---

## Fase 2 — Chunking

| Status | Tarefa |
|---|---|
| ✅ | Definir e documentar estratégia de chunking (tamanho, overlap) |
| ✅ | Implementar separação de texto prose vs. blocos de código |
| ✅ | Implementar `src/chunking/` |
| ✅ | Cobrir com testes unitários |

---

## Fase 3 — Embeddings

| Status | Tarefa |
|---|---|
| ⬜ | Escolher modelo de embeddings e justificar no `architecture.md` |
| ⬜ | Implementar `src/embeddings/` |
| ⬜ | Documentar integração em `docs/integration/` |

---

## Fase 4 — Data Quality Checks

| Status | Tarefa |
|---|---|
| ⬜ | Implementar descarte de chunks vazios / abaixo do tamanho mínimo |
| ⬜ | Implementar detecção de duplicatas antes da geração de embedding |
| ⬜ | Implementar métrica de cobertura de ingestão |
| ⬜ | Cobrir com testes unitários |

---

## Fase 5 — Vector DB e Retrieval

| Status | Tarefa |
|---|---|
| ⬜ | Configurar Chroma local |
| ⬜ | Implementar `src/retrieval/` — busca por similaridade + filtro por metadata |
| ⬜ | Documentar integração em `docs/integration/` |
| ⬜ | Teste de integração: caminho feliz + falha (timeout, resposta vazia) |

---

## Fase 6 — Orquestração (Airflow)

| Status | Tarefa |
|---|---|
| ⬜ | Criar DAG `dags/rag_pipeline_dag.py` |
| ⬜ | Sequência: `extract → chunk → embed → quality_check → load_to_vectordb` |
| ⬜ | Testar localmente com `astro dev start` |

---

## Fase 7 — Observabilidade e LLM

| Status | Tarefa |
|---|---|
| ⬜ | Implementar logging de latência por etapa |
| ⬜ | Implementar estimativa de custo de tokens |
| ⬜ | Implementar log de taxa de "sem resultado relevante" |
| ⬜ | Integrar LLM para geração de resposta final |
| ⬜ | Documentar integração em `docs/integration/` |

---

## Fase 8 — Documentação Final e Portfólio

| Status | Tarefa |
|---|---|
| ⬜ | Escrever README completo (diagrama, decisões, métricas, escala) |
| ⬜ | Revisar `docs/architecture.md` com decisões finais |
| ⬜ | Gravar demo ou escrever walkthrough |
