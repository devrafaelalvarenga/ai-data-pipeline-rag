# architecture — Document Intelligence Pipeline (RAG)

## Visão Geral

Pipeline de dados para alimentar um sistema de RAG (Retrieval-Augmented Generation) usando a documentação técnica do dbt como fonte. O diferencial do projeto é tratar a qualidade do retrieval como um problema de qualidade de dados — aplicando data quality checks antes de persistir os chunks no vector DB.

---

## Stack

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Linguagem | Python 3.12 | — |
| Gerenciador de pacotes | uv | Performance e determinismo no lock |
| Orquestração | Apache Airflow via Astro CLI | Open-source, familiar, maior presença em vagas |
| Vector DB | Chroma (local) | Gratuito, sem dependência de serviço externo, fácil de demonstrar em portfólio |
| Fonte de dados | dbt docs (GitHub, Markdown) | Estrutura hierárquica + blocos de código SQL/Jinja força chunking mais sofisticado |
| Embeddings | A definir | — |
| LLM | A definir | — |

---

## Fluxo de Dados

```
[dbt docs no GitHub]
        │
        ▼
[Ingestão — src/ingestion/]
  Pull de arquivos Markdown via API do GitHub
  Script idempotente (não reprocessa o que não mudou)
        │
        ▼
[Chunking — src/chunking/]
  Separação de texto prose vs. blocos de código
  Tamanho e overlap documentados e justificados
        │
        ▼
[Embeddings — src/embeddings/]
  Geração de vetores por chunk
        │
        ▼
[Data Quality Checks — src/quality_checks/]   ← diferencial
  - Descartar chunks vazios ou abaixo do tamanho mínimo
  - Detectar e remover duplicatas antes de gerar embedding
  - Medir cobertura de ingestão (% de docs processados)
        │
        ▼
[Vector DB — Chroma]
  Persistência local com metadata (fonte, path, chunk_index)
        │
        ▼
[Retrieval — src/retrieval/]
  Busca por similaridade (cosine distance)
  Filtro por metadata
        │
        ▼
[LLM — geração de resposta]
  Chunks relevantes + pergunta → resposta contextualizada
        │
        ▼
[Observabilidade]
  - Latência por etapa
  - Custo estimado de tokens
  - Taxa de "sem resultado relevante"
```

---

## DAG do Airflow

Arquivo: `dags/rag_pipeline_dag.py`

```
extract → chunk → embed → quality_check → load_to_vectordb
```

---

## Estrutura de Pastas

```
ai-data-pipeline-rag/
├── dags/                    # DAGs do Airflow
├── data/                    # dados brutos e processados (no .gitignore)
│   └── raw/
│       └── dbt_docs/        # arquivos .md baixados da API do GitHub
│           ├── data_modeling/
│           └── testing/
├── docs/                    # documentação do projeto
│   └── integration/         # uma subpasta por integração externa
├── notebooks/               # experimentação (sem exigência de teste formal)
├── src/
│   ├── ingestion/           # extração das docs do GitHub
│   │   └── dbt_docs_ingestion.py
│   ├── chunking/            # estratégia de divisão do texto
│   ├── embeddings/          # geração de embeddings
│   ├── quality_checks/      # checks de qualidade de dados
│   └── retrieval/           # busca no Chroma + resposta do LLM
├── tests/
├── .env                     # credenciais (nunca commitar preenchido)
├── pyproject.toml           # dependências e config de ferramentas (uv)
└── README.md
```

---

## Decisões de Arquitetura e Trade-offs

### Chroma vs. Pinecone / Weaviate
Chroma foi escolhido por ser local e gratuito — ideal para portfólio (qualquer pessoa pode rodar sem conta em serviço externo). Em produção, o equivalente gerenciado seria Pinecone ou Weaviate, com ganhos em escalabilidade e busca distribuída.

### Airflow via Astro CLI vs. Dagster
Airflow tem maior penetração em vagas e é familar. Dagster também é gratuito no core e tem melhor DX (assets, lineage nativo), mas a curva seria dupla neste momento. A troca futura é viável sem redesenhar o pipeline — basta reescrever os operadores.

### Markdown do GitHub vs. scraping de HTML
Markdown é mais limpo e estruturado. O scraping de HTML da doc renderizada introduz ruído (nav, rodapé, JS) e quebra com atualizações de layout. A API do GitHub é estável e retorna o conteúdo bruto.

### Chunking: prose vs. código separados
Blocos de código SQL/Jinja têm semântica diferente de texto corrido. Misturar os dois no mesmo chunk degrada a qualidade do embedding. A estratégia adotada trata cada tipo separadamente — decisão documentada e justificada no próprio módulo `src/chunking/`.
