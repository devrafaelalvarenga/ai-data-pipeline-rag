"""Testes unitários para src/ingestion/dbt_docs_ingestion.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import requests

import src.ingestion.dbt_docs_ingestion as ingestion
from src.ingestion.dbt_docs_ingestion import (
    RateLimitExceeded,
    download_file,
    ingest_section,
    list_markdown_files,
    run_ingestion,
)


# ---------------------------------------------------------------------------
# _request_headers
# ---------------------------------------------------------------------------


def test_request_headers_without_token():
    with patch.object(ingestion, "GITHUB_TOKEN", None):
        headers = ingestion._request_headers()
    assert headers == {"Accept": "application/vnd.github+json"}
    assert "Authorization" not in headers


def test_request_headers_with_token():
    with patch.object(ingestion, "GITHUB_TOKEN", "ghp_test123"):
        headers = ingestion._request_headers()
    assert headers["Authorization"] == "Bearer ghp_test123"
    assert headers["Accept"] == "application/vnd.github+json"


# ---------------------------------------------------------------------------
# list_markdown_files
# ---------------------------------------------------------------------------

API_ITEMS = [
    {"type": "file", "name": "models.md", "download_url": "https://raw.example.com/models.md"},
    {"type": "file", "name": "sources.md", "download_url": "https://raw.example.com/sources.md"},
    {"type": "file", "name": "config.yml", "download_url": "https://raw.example.com/config.yml"},
    {"type": "dir", "name": "subdir", "download_url": None},
]


def _mock_response(status_code=200, json_data=None, text="", headers=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = text
    mock.json.return_value = json_data or []
    mock.headers = headers or {}
    if status_code >= 400:
        mock.raise_for_status.side_effect = requests.HTTPError(response=mock)
    else:
        mock.raise_for_status.return_value = None
    return mock


def test_list_markdown_files_returns_only_md_files():
    with patch("requests.get", return_value=_mock_response(json_data=API_ITEMS)):
        result = list_markdown_files("website/docs/docs/build")
    names = [item["name"] for item in result]
    assert names == ["models.md", "sources.md"]


def test_list_markdown_files_excludes_directories():
    with patch("requests.get", return_value=_mock_response(json_data=API_ITEMS)):
        result = list_markdown_files("website/docs/docs/build")
    assert all(item["type"] == "file" for item in result)


def test_list_markdown_files_empty_section():
    with patch("requests.get", return_value=_mock_response(json_data=[])):
        result = list_markdown_files("website/docs/docs/build")
    assert result == []


def test_list_markdown_files_raises_rate_limit_exceeded():
    mock = _mock_response(
        status_code=403,
        text="rate limit exceeded",
        headers={"x-ratelimit-reset": "1720000000"},
    )
    with patch("requests.get", return_value=mock):
        with pytest.raises(RateLimitExceeded, match="(?i)rate limit"):
            list_markdown_files("website/docs/docs/build")


def test_list_markdown_files_403_not_rate_limit_raises_http_error():
    mock = _mock_response(status_code=403, text="forbidden")
    with patch("requests.get", return_value=mock):
        with pytest.raises(requests.HTTPError):
            list_markdown_files("website/docs/docs/build")


def test_list_markdown_files_404_raises_http_error():
    mock = _mock_response(status_code=404)
    with patch("requests.get", return_value=mock):
        with pytest.raises(requests.HTTPError):
            list_markdown_files("website/docs/docs/build")


# ---------------------------------------------------------------------------
# download_file
# ---------------------------------------------------------------------------

FAKE_ITEM = {
    "name": "models.md",
    "download_url": "https://raw.example.com/models.md",
}

FAKE_CONTENT = "# Models\n\nConteúdo de exemplo."


def test_download_file_creates_directory_and_file(tmp_path):
    dest = tmp_path / "data_modeling"
    with patch("requests.get", return_value=_mock_response(text=FAKE_CONTENT)):
        result = download_file(FAKE_ITEM, dest)
    assert result == dest / "models.md"
    assert result.read_text(encoding="utf-8") == FAKE_CONTENT


def test_download_file_creates_nested_directory(tmp_path):
    dest = tmp_path / "a" / "b" / "c"
    with patch("requests.get", return_value=_mock_response(text=FAKE_CONTENT)):
        download_file(FAKE_ITEM, dest)
    assert dest.exists()


def test_download_file_is_idempotent(tmp_path):
    dest = tmp_path / "data_modeling"
    with patch("requests.get", return_value=_mock_response(text=FAKE_CONTENT)):
        download_file(FAKE_ITEM, dest)
    updated_content = "# Atualizado"
    with patch("requests.get", return_value=_mock_response(text=updated_content)):
        result = download_file(FAKE_ITEM, dest)
    assert result.read_text(encoding="utf-8") == updated_content


def test_download_file_raises_on_http_error(tmp_path):
    dest = tmp_path / "data_modeling"
    with patch("requests.get", return_value=_mock_response(status_code=500)):
        with pytest.raises(requests.HTTPError):
            download_file(FAKE_ITEM, dest)


# ---------------------------------------------------------------------------
# ingest_section
# ---------------------------------------------------------------------------

FAKE_FILES = [
    {"name": "models.md", "type": "file", "download_url": "https://raw.example.com/models.md"},
    {"name": "sources.md", "type": "file", "download_url": "https://raw.example.com/sources.md"},
]


def test_ingest_section_returns_list_of_paths(tmp_path):
    with (
        patch.object(ingestion, "RAW_DATA_DIR", tmp_path),
        patch(
            "src.ingestion.dbt_docs_ingestion.list_markdown_files",
            return_value=FAKE_FILES,
        ),
        patch(
            "src.ingestion.dbt_docs_ingestion.download_file",
            side_effect=lambda item, dest: dest / item["name"],
        ),
    ):
        result = ingest_section("Data Modeling", "website/docs/docs/build")

    assert len(result) == 2
    assert all(isinstance(p, Path) for p in result)


def test_ingest_section_uses_normalized_directory_name(tmp_path):
    captured_dirs = []

    def capture_dir(item, dest):
        captured_dirs.append(dest)
        return dest / item["name"]

    with (
        patch.object(ingestion, "RAW_DATA_DIR", tmp_path),
        patch(
            "src.ingestion.dbt_docs_ingestion.list_markdown_files",
            return_value=FAKE_FILES,
        ),
        patch("src.ingestion.dbt_docs_ingestion.download_file", side_effect=capture_dir),
    ):
        ingest_section("Data Modeling", "website/docs/docs/build")

    assert all(d == tmp_path / "data_modeling" for d in captured_dirs)


def test_ingest_section_empty_returns_empty_list(tmp_path):
    with (
        patch.object(ingestion, "RAW_DATA_DIR", tmp_path),
        patch(
            "src.ingestion.dbt_docs_ingestion.list_markdown_files",
            return_value=[],
        ),
    ):
        result = ingest_section("Data Modeling", "website/docs/docs/build")

    assert result == []


# ---------------------------------------------------------------------------
# run_ingestion
# ---------------------------------------------------------------------------


def test_run_ingestion_calls_ingest_section_for_each_section():
    fake_sections = {
        "Data Modeling": "path/a",
        "Testing": "path/b",
    }
    with (
        patch.object(ingestion, "SECTIONS", fake_sections),
        patch(
            "src.ingestion.dbt_docs_ingestion.ingest_section",
            return_value=[],
        ) as mock_ingest,
    ):
        result = run_ingestion()

    assert mock_ingest.call_count == 2
    mock_ingest.assert_any_call("Data Modeling", "path/a")
    mock_ingest.assert_any_call("Testing", "path/b")
    assert set(result.keys()) == {"Data Modeling", "Testing"}


def test_run_ingestion_returns_dict_keyed_by_section():
    fake_sections = {"Alpha": "path/alpha"}
    fake_paths = [Path("data/raw/alpha/file.md")]
    with (
        patch.object(ingestion, "SECTIONS", fake_sections),
        patch(
            "src.ingestion.dbt_docs_ingestion.ingest_section",
            return_value=fake_paths,
        ),
    ):
        result = run_ingestion()

    assert result == {"Alpha": fake_paths}
