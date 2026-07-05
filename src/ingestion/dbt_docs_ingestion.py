"""
Ingestão de documentação técnica do dbt (dbt-labs/docs.getdbt.com) via API do GitHub.

Escopo (Semana 1): baixar seções específicas em Markdown para uma pasta local,
de forma idempotente. Chunking, embeddings e vector DB ficam para as próximas etapas.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = "dbt-labs/docs.getdbt.com"
BRANCH = "current"
BASE_API_URL = f"https://api.github.com/repos/{REPO}/contents"

# Sem token: 60 req/hora por IP. Com token (mesmo sem permissões especiais): 5.000 req/hora.
# Configurar em .env como GITHUB_TOKEN=ghp_xxx (token simples, "no scopes" já basta para repos públicos).
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def _request_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


class RateLimitExceeded(RuntimeError):
    """Levantado quando a API do GitHub bloqueia por limite de requisições."""

# Seções escolhidas para o escopo inicial do projeto.
# Caminho relativo dentro do repositório -> pasta local de destino.
SECTIONS = {
    "Data Modeling": "website/docs/docs/build",
    "Testing": "website/docs/docs/build",  # dbt agrupa "data tests" dentro de build/
}

RAW_DATA_DIR = Path("data/raw/dbt_docs")


def list_markdown_files(section_path: str) -> list[dict]:
    """Lista os arquivos .md de uma seção do repositório via API do GitHub."""
    url = f"{BASE_API_URL}/{section_path}?ref={BRANCH}"
    response = requests.get(url, headers=_request_headers(), timeout=30)

    if response.status_code == 403 and "rate limit" in response.text.lower():
        reset_header = response.headers.get("x-ratelimit-reset")
        raise RateLimitExceeded(
            "Rate limit da API do GitHub excedido. "
            "Configure GITHUB_TOKEN no .env para subir o limite de 60 para 5.000 req/hora. "
            f"(reset em: {reset_header})"
        )
    response.raise_for_status()

    items = response.json()
    return [item for item in items if item["type"] == "file" and item["name"].endswith(".md")]


def download_file(item: dict, destination_dir: Path) -> Path:
    """Baixa um único arquivo Markdown, sobrescrevendo se já existir (idempotente)."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / item["name"]

    response = requests.get(item["download_url"], headers=_request_headers(), timeout=30)
    response.raise_for_status()

    destination_path.write_text(response.text, encoding="utf-8")
    return destination_path


def ingest_section(section_name: str, section_path: str) -> list[Path]:
    """Baixa todos os arquivos .md de uma seção específica."""
    logger.info("Listando arquivos da seção '%s' (%s)", section_name, section_path)
    files = list_markdown_files(section_path)

    destination_dir = RAW_DATA_DIR / section_name.lower().replace(" ", "_")
    downloaded_paths = []

    for item in files:
        path = download_file(item, destination_dir)
        downloaded_paths.append(path)
        logger.info("  -> baixado: %s", path)

    logger.info("Seção '%s': %d arquivo(s) baixado(s)", section_name, len(downloaded_paths))
    return downloaded_paths


def run_ingestion() -> dict[str, list[Path]]:
    """Ponto de entrada principal. Roda de novo não duplica nem quebra (idempotente)."""
    results = {}
    for section_name, section_path in SECTIONS.items():
        results[section_name] = ingest_section(section_name, section_path)
    return results


if __name__ == "__main__":
    run_ingestion()