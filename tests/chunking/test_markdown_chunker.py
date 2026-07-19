"""Testes unitários para src/chunking/markdown_chunker.py."""

from __future__ import annotations

from src.chunking.markdown_chunker import (
    Chunk,
    chunk_all,
    chunk_code,
    chunk_document,
    chunk_prose,
    parse_frontmatter,
    split_prose_and_code,
)

# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------


def test_parse_frontmatter_extracts_known_fields():
    text = (
        '---\ntitle: "Cumulative metrics"\nid: cumulative\n'
        'description: "Aggregate a metric"\nsidebar_label: Cumulative\n---\n'
        "Conteúdo do documento."
    )
    metadata, body = parse_frontmatter(text)
    assert metadata == {
        "title": "Cumulative metrics",
        "id": "cumulative",
        "description": "Aggregate a metric",
    }
    assert body == "Conteúdo do documento."


def test_parse_frontmatter_ignores_unknown_fields():
    text = "---\ntitle: Foo\ntags: [a, b]\n---\nCorpo."
    metadata, _ = parse_frontmatter(text)
    assert metadata == {"title": "Foo"}


def test_parse_frontmatter_without_frontmatter_returns_empty_metadata():
    text = "# Título\n\nSem frontmatter aqui."
    metadata, body = parse_frontmatter(text)
    assert metadata == {}
    assert body == text


# ---------------------------------------------------------------------------
# split_prose_and_code
# ---------------------------------------------------------------------------


def test_split_prose_and_code_pure_prose():
    body = "Parágrafo um.\n\nParágrafo dois."
    blocks = split_prose_and_code(body)
    assert len(blocks) == 1
    assert blocks[0].block_type == "prose"
    assert blocks[0].content == body


def test_split_prose_and_code_alternates_blocks():
    body = "Antes do código.\n\n```sql\nselect 1\n```\n\nDepois do código."
    blocks = split_prose_and_code(body)
    assert [b.block_type for b in blocks] == ["prose", "code", "prose"]
    assert blocks[1].content == "select 1\n"
    assert blocks[1].language == "sql"


def test_split_prose_and_code_language_defaults_to_none():
    body = "```\nplain block\n```"
    blocks = split_prose_and_code(body)
    assert blocks[0].language is None


def test_split_prose_and_code_consecutive_code_blocks_no_empty_prose():
    body = "```yaml\na: 1\n```\n```yaml\nb: 2\n```"
    blocks = split_prose_and_code(body)
    assert [b.block_type for b in blocks] == ["code", "code"]


def test_split_prose_and_code_skips_empty_code_block():
    body = "Texto antes.\n\n```\n\n```\n\nTexto depois."
    blocks = split_prose_and_code(body)
    assert [b.block_type for b in blocks] == ["prose", "prose"]


# ---------------------------------------------------------------------------
# chunk_prose
# ---------------------------------------------------------------------------


def test_chunk_prose_short_text_fits_single_chunk():
    text = "Parágrafo curto.\n\nOutro parágrafo curto."
    chunks = chunk_prose(text, max_chars=1000, overlap_chars=150)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_prose_splits_when_exceeds_max_chars():
    paragraphs = [
        f"Parágrafo número {i} com algum conteúdo de exemplo." for i in range(20)
    ]
    text = "\n\n".join(paragraphs)
    chunks = chunk_prose(text, max_chars=200, overlap_chars=30)
    assert len(chunks) > 1
    # overlap pode ligeiramente exceder max_chars puro
    assert all(len(c) <= 200 + 30 for c in chunks)


def test_chunk_prose_has_overlap_between_consecutive_chunks():
    paragraphs = [f"Parágrafo {i}: " + ("x" * 40) for i in range(10)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_prose(text, max_chars=150, overlap_chars=40)
    assert len(chunks) > 1
    tail_of_first = chunks[0][-40:]
    assert tail_of_first in chunks[1]


def test_chunk_prose_hard_splits_paragraph_longer_than_max_chars():
    long_paragraph = "a" * 500
    chunks = chunk_prose(long_paragraph, max_chars=200, overlap_chars=50)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)
    # sem o overlap de cada chunk (exceto o 1º), a concatenação reconstrói o original
    reconstructed = chunks[0] + "".join(c[50:] for c in chunks[1:])
    assert reconstructed == long_paragraph


def test_chunk_prose_empty_text_returns_no_chunks():
    assert chunk_prose("   \n\n   ") == []


# ---------------------------------------------------------------------------
# chunk_code
# ---------------------------------------------------------------------------


def test_chunk_code_short_block_returned_unchanged():
    code = "select *\nfrom {{ ref('orders') }}"
    chunks = chunk_code(code, max_chars=1000, overlap_lines=2)
    assert chunks == [code]


def test_chunk_code_splits_long_block_by_line():
    lines = [f"line_{i} = {i}" for i in range(100)]
    code = "\n".join(lines)
    chunks = chunk_code(code, max_chars=200, overlap_lines=2)
    assert len(chunks) > 1
    # cada linha de cada chunk deve ser uma linha original intacta (nunca cortada)
    for chunk in chunks:
        for line in chunk.splitlines():
            assert line in lines


def test_chunk_code_overlap_lines_repeated_between_chunks():
    lines = [f"line_{i} = {i}" for i in range(100)]
    code = "\n".join(lines)
    chunks = chunk_code(code, max_chars=200, overlap_lines=2)
    first_chunk_lines = chunks[0].splitlines()
    second_chunk_lines = chunks[1].splitlines()
    assert first_chunk_lines[-2:] == second_chunk_lines[:2]


# ---------------------------------------------------------------------------
# chunk_document
# ---------------------------------------------------------------------------


def test_chunk_document_extracts_title_and_mixed_blocks(tmp_path):
    content = (
        '---\ntitle: "Exemplo"\n---\n'
        "Texto de introdução ao documento.\n\n"
        "```sql\nselect 1\n```\n\n"
        "Texto de conclusão."
    )
    file_path = tmp_path / "exemplo.md"
    file_path.write_text(content, encoding="utf-8")

    chunks = chunk_document(file_path)

    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.doc_title == "Exemplo" for c in chunks)
    assert all(c.source_file == str(file_path) for c in chunks)
    assert [c.chunk_type for c in chunks] == ["prose", "code", "prose"]
    assert [c.chunk_index for c in chunks] == [0, 1, 2]
    assert chunks[1].language == "sql"
    assert chunks[0].language is None


def test_chunk_document_without_frontmatter_has_no_title(tmp_path):
    file_path = tmp_path / "sem_frontmatter.md"
    file_path.write_text("Só texto simples.", encoding="utf-8")

    chunks = chunk_document(file_path)

    assert len(chunks) == 1
    assert chunks[0].doc_title is None


# ---------------------------------------------------------------------------
# chunk_all
# ---------------------------------------------------------------------------


def test_chunk_all_walks_directory_recursively(tmp_path):
    section_dir = tmp_path / "data_modeling"
    section_dir.mkdir()
    (section_dir / "a.md").write_text("Conteúdo A.", encoding="utf-8")
    (section_dir / "b.md").write_text(
        "Conteúdo B.\n\n```sql\nselect 1\n```", encoding="utf-8"
    )

    chunks = chunk_all(tmp_path)

    sources = {c.source_file for c in chunks}
    assert sources == {str(section_dir / "a.md"), str(section_dir / "b.md")}


def test_chunk_all_empty_directory_returns_empty_list(tmp_path):
    assert chunk_all(tmp_path) == []
