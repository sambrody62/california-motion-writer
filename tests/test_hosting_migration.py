"""
Tests for the Supabase/Render hosting migration:
- DATABASE_URL env-var support with scheme normalization and pooler handling
- Supabase Storage backend for evidence files
"""
from unittest.mock import MagicMock, patch

import pytest

from app.core.database import Database, _connect_args_for, _normalize_database_url
from app.services import evidence_storage_service


class TestDatabaseUrlNormalization:
    def test_postgres_scheme_gets_asyncpg_driver(self):
        assert _normalize_database_url("postgres://u:p@host:5432/db") == (
            "postgresql+asyncpg://u:p@host:5432/db"
        )

    def test_postgresql_scheme_gets_asyncpg_driver(self):
        assert _normalize_database_url("postgresql://u:p@host:5432/db") == (
            "postgresql+asyncpg://u:p@host:5432/db"
        )

    def test_asyncpg_url_unchanged(self):
        url = "postgresql+asyncpg://u:p@host:5432/db"
        assert _normalize_database_url(url) == url

    def test_sqlite_url_unchanged(self):
        url = "sqlite+aiosqlite:///./local.db"
        assert _normalize_database_url(url) == url


class TestPoolerConnectArgs:
    def test_supabase_pooler_port_disables_statement_cache(self):
        # pgBouncer (transaction mode, port 6543) can't cache prepared statements
        args = _connect_args_for("postgresql+asyncpg://u:p@db.x.supabase.co:6543/postgres")
        assert args == {"statement_cache_size": 0}

    def test_direct_connection_has_no_extra_args(self):
        assert _connect_args_for("postgresql+asyncpg://u:p@db.x.supabase.co:5432/postgres") == {}

    def test_sqlite_has_no_extra_args(self):
        assert _connect_args_for("sqlite+aiosqlite:///:memory:") == {}


class TestDatabaseUrlEnvPreferred:
    async def test_database_url_env_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        database = Database()
        await database.init()
        try:
            assert str(database.engine.url) == "sqlite+aiosqlite:///:memory:"
        finally:
            await database.engine.dispose()


class TestSupabaseStorageBackend:
    def _configure(self, monkeypatch):
        monkeypatch.setenv("STORAGE_BACKEND", "supabase")
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")
        monkeypatch.setenv("SUPABASE_EVIDENCE_BUCKET", "evidence")

    def test_supabase_backend_uploads_and_returns_path(self, monkeypatch):
        self._configure(monkeypatch)
        response = MagicMock(status_code=200)
        with patch("httpx.post", return_value=response) as post:
            path = evidence_storage_service.save_file("motion-1", "shot.png", b"bytes")
        assert path == "supabase://evidence/evidence/motion-1/shot.png"
        url = post.call_args.args[0]
        assert url == "https://example.supabase.co/storage/v1/object/evidence/evidence/motion-1/shot.png"
        headers = post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer service-key"

    def test_supabase_backend_sanitizes_filename(self, monkeypatch):
        self._configure(monkeypatch)
        response = MagicMock(status_code=200)
        with patch("httpx.post", return_value=response) as post:
            path = evidence_storage_service.save_file("motion-1", "../../etc/passwd", b"x")
        assert "etc" not in post.call_args.args[0].replace("passwd", "")
        assert path.endswith("/passwd")

    def test_supabase_failure_raises_without_disk_fallback(self, monkeypatch, tmp_path):
        # A silent local fallback loses files on ephemeral hosting while the
        # DB row claims they exist — failures must surface to the caller.
        self._configure(monkeypatch)
        monkeypatch.chdir(tmp_path)
        with patch("httpx.post", side_effect=RuntimeError("network down")):
            with pytest.raises(evidence_storage_service.EvidenceStorageError):
                evidence_storage_service.save_file("motion-1", "a.txt", b"data")
        assert not (tmp_path / "uploads").exists()

    def test_default_backend_unchanged_without_flag(self, monkeypatch, tmp_path):
        monkeypatch.delenv("STORAGE_BACKEND", raising=False)
        monkeypatch.chdir(tmp_path)
        path = evidence_storage_service.save_file("motion-2", "b.txt", b"data")
        assert (tmp_path / "uploads" / "motion-2" / "b.txt").exists()
        assert "supabase" not in path
