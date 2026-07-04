# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
> Este arquivo é o ponto de entrada da IA para este projeto.
> Ele funciona como um índice: não contém detalhes longos — aponta para os documentos certos.
> Toda instrução longa ou técnica vive em docs/. Este arquivo deve permanecer enxuto.

## 🗂️ Índice de Documentos Obrigatórios

> A IA deve ler todos os arquivos abaixo antes de executar qualquer tarefa.

| Arquivo | Descrição | Atualizado em |
|---|---|---|
| `docs/architecture.md` | Stack, fluxo de dados e detalhamento de cada camada | 04/07/2026 às 00h00 BRT |
| `docs/roadmap.md` | Tarefas pendentes, em andamento e concluídas | 04/07/2026 às 01h00 BRT |
| `docs/changes.md` | Changelog de todas as alterações relevantes | 04/07/2026 às 01h00 BRT |
| `docs/integration/README.md` | Índice de todas as integrações externas documentadas | 04/07/2026 às 00h00 BRT |

> Regra: toda vez que um arquivo acima for alterado, atualizar imediatamente o campo "Atualizado em" com a data e hora no fuso BRT (ex: `20/03/2025 às 14h32 BRT`). Ao final de cada sessão, checar se algum arquivo do índice foi modificado e confirmar que o timestamp reflete isso.

-----

## 🛠️ Stack e Ambiente

- **Linguagem:** Python 3.12
- **Gerenciador de pacotes:** uv
- **Orquestração:** Apache Airflow via Astro CLI (ambiente local containerizado)
- **Vector DB:** Chroma (local)
- **Fonte de dados do projeto:** documentação técnica do dbt (via GitHub)
- **Rodar testes:** `uv run pytest tests/ -v`
- **Lint/format:** `uv run ruff check . --fix && uv run ruff format .`
- **Subir ambiente localmente:** `astro dev start`
- **Parar ambiente:** `astro dev stop`

-----

## 🧠 Como a IA deve se comunicar

- Sou Data Engenheiro em transição para AI Data Engineering — **não preciso de explicação de conceitos básicos** de programação, SQL, Python ou pipelines de dados tradicionais (ETL, orquestração, warehousing).
- **Explicar em detalhe apenas conceitos específicos do universo de IA/LLM** ainda não dominados: embeddings, estratégias de chunking, funcionamento de vector DBs, RAG, LLMOps.
- Ir direto ao ponto: priorizar objetividade e justificativa técnica das decisões em vez de explicações longas.
- Quando sugerir uma abordagem técnica, expor brevemente o trade-off (por que essa opção e não outra), pois isso alimenta decisões que preciso defender depois.
- Responder sempre em Português do Brasil.

-----

## 📋 Regras Obrigatórias

### Documentação

- [ ] Toda alteração na estrutura de tabelas, funções, triggers ou fluxo de dados → atualizar `docs/architecture.md`
- [ ] Toda etapa concluída ou iniciada → atualizar `docs/roadmap.md`
- [ ] Toda mudança relevante → registrar em `docs/changes.md` com data e descrição
- [ ] Todo novo documento criado → referenciar no índice deste arquivo com a data
- [ ] Este arquivo (`CLAUDE.md`) deve permanecer enxuto — nunca adicionar conteúdo longo aqui

### Código

- [ ] Proibido hardcode de credenciais, chaves de API ou strings de conexão — sempre via `.env`
- [ ] Proibido hardcode de paths absolutos — usar variáveis de ambiente ou config
- [ ] Tudo precisa ser documentado — funções, componentes, lógicas complexas e decisões de architecture
- [ ] Decisões de chunking, escolha de vector DB, estratégia de orquestração → justificar no `docs/architecture.md`, não só no código

### Integrações

- [ ] Toda integração com serviço externo deve ser pesquisada na documentação oficial antes de ser implementada
- [ ] Toda integração deve ser documentada dentro de `docs/integration/` com um arquivo próprio
- [ ] O arquivo `docs/integration/README.md` deve ser atualizado com o índice de integrações

### Ambiente e Infraestrutura

- [ ] Criar e manter o arquivo `.env` com todas as chaves necessárias já estruturadas e comentadas, deixando os valores em branco para preenchimento manual
- [ ] Nunca commitar `.env` preenchido — garantir que está no `.gitignore`

-----

## 🧪 Padrão de Testes

> Nível de exigência proporcional ao contexto — código de produção precisa de rigor, experimentação não.

- **`src/` (pipeline de produção):** cobertura obrigatória de testes unitários para lógica de chunking, quality checks e transformações de dados
- **`notebooks/` (experimentação):** isento de teste formal
- **Integrações externas (vector DB, APIs de embedding):** teste de integração cobrindo o caminho feliz + pelo menos 1 caso de falha (timeout, resposta vazia, rate limit)
- Casos críticos ou com lógica complexa → sempre testar, independente da pasta

-----

## Setup

Todos os comandos devem ser executados dentro de `ai-data-pipeline-rag/`.