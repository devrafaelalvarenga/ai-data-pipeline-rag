"""
Chunking da documentação do dbt baixada em Markdown (src/ingestion/).

Estratégia (ver justificativa em docs/architecture.md):
- Prose e blocos de código (```lang ... ```) são tratados separadamente:
  misturar os dois no mesmo chunk degrada a qualidade do embedding.
- Prose: chunks de até MAX_PROSE_CHARS caracteres, respeitando limites de
  parágrafo sempre que possível, com overlap de PROSE_OVERLAP_CHARS para
  preservar contexto entre chunks vizinhos.
- Código: mantido inteiro sempre que couber em MAX_CODE_CHARS; blocos maiores
  são divididos por linha (nunca no meio de uma linha), com overlap de
  CODE_OVERLAP_LINES linhas.
- O tamanho é medido em caracteres, não em tokens: o modelo de embeddings
  ainda não foi escolhido (Fase 3). Caracteres são uma proxy simples e
  determinística; a conversão para um budget de tokens fica para quando o
  modelo for definido.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw/dbt_docs")

MAX_PROSE_CHARS = 1000
PROSE_OVERLAP_CHARS = 150

MAX_CODE_CHARS = 1000
CODE_OVERLAP_LINES = 2

FRONTMATTER_PATTERN = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
CODE_FENCE_PATTERN = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
FRONTMATTER_FIELDS = ("title", "description", "id")


@dataclass
class RawBlock:
    """Um trecho de um documento já separado em prose ou código."""

    block_type: str  # "prose" | "code"
    content: str
    language: str | None = None


@dataclass
class Chunk:
    """Unidade final persistida no vector DB (Fase 5)."""

    content: str
    chunk_type: str  # "prose" | "code"
    chunk_index: int
    source_file: str
    doc_title: str | None = None
    language: str | None = None


# ---------------------------------------------------------------------------
# frontmatter
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Separa o frontmatter YAML (se houver) do corpo do documento.

    Extrai apenas os campos usados como metadata de chunk (FRONTMATTER_FIELDS);
    não faz parsing YAML completo pois o restante do frontmatter não é usado.
    """
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        if key in FRONTMATTER_FIELDS:
            metadata[key] = value.strip().strip('"')

    return metadata, text[match.end() :]


# ---------------------------------------------------------------------------
# separação prose / código
# ---------------------------------------------------------------------------


def split_prose_and_code(body: str) -> list[RawBlock]:
    """Divide o corpo do documento em blocos alternados de prose e código."""
    blocks: list[RawBlock] = []
    cursor = 0

    for match in CODE_FENCE_PATTERN.finditer(body):
        prose = body[cursor : match.start()]
        if prose.strip():
            blocks.append(RawBlock("prose", prose))

        code = match.group(2)
        if code.strip():
            blocks.append(RawBlock("code", code, language=match.group(1) or None))

        cursor = match.end()

    trailing = body[cursor:]
    if trailing.strip():
        blocks.append(RawBlock("prose", trailing))

    return blocks


# ---------------------------------------------------------------------------
# chunking de prose
# ---------------------------------------------------------------------------


def _sliding_window_split(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Corta `text` em pedaços de até `max_chars`, repetindo `overlap_chars`
    do fim de um pedaço no início do próximo. Usado quando um único
    parágrafo/linha já excede o tamanho máximo do chunk."""
    if len(text) <= max_chars:
        return [text]

    step = max_chars - overlap_chars
    pieces = []
    start = 0
    while start < len(text):
        pieces.append(text[start : start + max_chars])
        if start + max_chars >= len(text):
            break
        start += step
    return pieces


def chunk_prose(
    text: str,
    max_chars: int = MAX_PROSE_CHARS,
    overlap_chars: int = PROSE_OVERLAP_CHARS,
) -> list[str]:
    """Agrupa parágrafos em chunks de até `max_chars`, com overlap entre
    chunks consecutivos para preservar contexto na fronteira."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            overlap = current[-overlap_chars:]
            candidate = f"{overlap}\n\n{paragraph}"

        if len(candidate) <= max_chars:
            current = candidate
        else:
            pieces = _sliding_window_split(candidate, max_chars, overlap_chars)
            chunks.extend(pieces[:-1])
            current = pieces[-1]

    if current:
        chunks.append(current)

    return chunks


# ---------------------------------------------------------------------------
# chunking de código
# ---------------------------------------------------------------------------


def chunk_code(
    text: str, max_chars: int = MAX_CODE_CHARS, overlap_lines: int = CODE_OVERLAP_LINES
) -> list[str]:
    """Mantém o bloco de código inteiro se couber em `max_chars`. Caso
    contrário, divide por linha (nunca no meio de uma linha), repetindo as
    últimas `overlap_lines` linhas no início do chunk seguinte."""
    if len(text) <= max_chars:
        return [text]

    lines = text.splitlines()
    chunks: list[str] = []
    current: list[str] = []

    for line in lines:
        candidate = current + [line]
        if len("\n".join(candidate)) <= max_chars or not current:
            current = candidate
            continue

        chunks.append("\n".join(current))
        current = current[-overlap_lines:] + [line] if overlap_lines else [line]

    if current:
        chunks.append("\n".join(current))

    return chunks


# ---------------------------------------------------------------------------
# orquestração por documento / diretório
# ---------------------------------------------------------------------------


def chunk_document(file_path: Path) -> list[Chunk]:
    """Lê um arquivo Markdown e retorna seus chunks (prose + código)."""
    text = file_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    blocks = split_prose_and_code(body)

    chunks: list[Chunk] = []
    for block in blocks:
        pieces = (
            chunk_prose(block.content)
            if block.block_type == "prose"
            else chunk_code(block.content)
        )
        for piece in pieces:
            content = piece.strip("\n")
            if not content.strip():
                continue
            chunks.append(
                Chunk(
                    content=content,
                    chunk_type=block.block_type,
                    chunk_index=len(chunks),
                    source_file=str(file_path),
                    doc_title=metadata.get("title"),
                    language=block.language if block.block_type == "code" else None,
                )
            )

    return chunks


def chunk_all(raw_dir: Path = RAW_DATA_DIR) -> list[Chunk]:
    """Ponto de entrada principal: aplica chunk_document a todos os .md
    encontrados recursivamente em `raw_dir`."""
    all_chunks: list[Chunk] = []

    for file_path in sorted(raw_dir.rglob("*.md")):
        chunks = chunk_document(file_path)
        all_chunks.extend(chunks)
        logger.info("  -> %s: %d chunk(s)", file_path, len(chunks))

    logger.info("Chunking concluído: %d chunk(s) no total", len(all_chunks))
    return all_chunks


if __name__ == "__main__":
    chunk_all()
