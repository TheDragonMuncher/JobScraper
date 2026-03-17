"""
db.py — Generic reusable SQLite utility
========================================
Features:
  • Singleton connection pool (thread-safe via threading.local)
  • Schema migration runner (append-only versioned migrations)
  • Context manager for automatic commit / rollback
  • Fluent query builder (SELECT / INSERT / UPDATE / DELETE)

Usage
-----
    from db import get_db, QueryBuilder

    db = get_db()

    # Query builder
    rows = (
        QueryBuilder("users")
        .select("id", "name", "email")
        .where("active = ?", 1)
        .order_by("name")
        .limit(10)
        .fetchall(db)
    )

    # Insert
    new_id = QueryBuilder("users").insert(db, name="Alice", email="alice@example.com")

    # Update
    QueryBuilder("users").where("id = ?", new_id).update(db, name="Alicia")

    # Delete
    QueryBuilder("users").where("id = ?", new_id).delete(db)

    # Raw SQL (escape hatch)
    with db.transaction() as cur:
        cur.execute("PRAGMA integrity_check;")
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Migrations — append new strings to add schema versions; never edit old ones.
# ---------------------------------------------------------------------------

MIGRATIONS: list[str] = [ ### change table structure ###
    # v1 — example users table
    """
    CREATE TABLE IF NOT EXISTS job_postings (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        source     varchar(256),
        title      varchar(64),
        company    varchar(64),
        location   varchar(64),
        job_type   varchar(64),
        seniority  varchar(64),
        salary_min integer,
        salary_max integer,
        description mediumtext,
        skills     mediumtext,
        url        varchar(256),
        posted_at  datetime,
        scraped_at datetime,
        raw_html   mediumtext
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
    """
]


# ---------------------------------------------------------------------------
# Connection pool — one connection per thread, one Database singleton
# ---------------------------------------------------------------------------

class _Pool:
    """Thread-local SQLite connection pool."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._local = threading.local()

    @property
    def connection(self) -> sqlite3.Connection:
        if not getattr(self._local, "conn", None):
            conn = sqlite3.connect(
                self._path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;") ### investigate code, ensure proper functionality ###
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA busy_timeout=5000;")
            self._local.conn = conn
            logger.debug("Opened connection on thread %s", threading.get_ident())
        return self._local.conn

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn:
            conn.close() ### investigate code, ensure proper functionality ###
            self._local.conn = None
            logger.debug("Closed connection on thread %s", threading.get_ident())


class Database:
    """
    Singleton database handle.

    Obtain via ``get_db()``. Do not instantiate directly after the first call
    unless you want a different database file.
    """

    _instance: Optional["Database"] = None
    _lock = threading.Lock()
    _pool = _Pool(Path("app.db"))

    def __new__(cls, path: Path = Path("app.db")) -> "Database":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._pool = _Pool(path) ### investigate code, ensure proper functionality ###
                inst._migrated = False
                cls._instance = inst
        return cls._instance

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def conn(self) -> sqlite3.Connection:
        if not self._migrated:
            with Database._lock:
                if not self._migrated: ### investigate code, ensure proper functionality ###
                    self._run_migrations()
                    self._migrated = True
        return self._pool.connection

    def close(self) -> None:
        """Close the current thread's connection."""
        self._pool.close() ### investigate code, ensure proper functionality ###

    def reset(self) -> None:
        """Tear down the singleton — useful in tests."""
        self._pool.close()
        Database._instance = None ### investigate code, ensure proper functionality ###

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Yields a cursor inside a transaction.
        Commits on clean exit, rolls back on any exception.

        Example::

            with db.transaction() as cur:
                cur.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
        """
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            logger.exception("Transaction rolled back")
            raise
        finally:
            cursor.close()

    # ------------------------------------------------------------------
    # Raw query helpers (read-only — no transaction needed)
    # ------------------------------------------------------------------

    def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchone()

    def scalar(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        row = self.fetchone(sql, params)
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Migration runner
    # ------------------------------------------------------------------

    def _run_migrations(self) -> None:
        conn = self._pool.connection
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                version    INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()

        current: int = conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM _schema_migrations;"
        ).fetchone()[0]

        for version, sql in enumerate(MIGRATIONS, start=1):
            if version <= current:
                continue
            try:
                conn.executescript(sql)          # executescript auto-commits
                conn.execute(
                    "INSERT INTO _schema_migrations (version) VALUES (?);", (version,)
                )
                conn.commit()
                logger.info("Applied migration v%d", version)
            except Exception:
                logger.exception("Failed to apply migration v%d", version)
                raise


# ---------------------------------------------------------------------------
# Query Builder
# ---------------------------------------------------------------------------

class QueryBuilder:
    """
    Fluent, composable SQL query builder for SQLite.

    Supports SELECT, INSERT, UPDATE, DELETE.  All clause methods return
    ``self`` so calls can be chained.

    Examples::

        # SELECT
        rows = (
            QueryBuilder("orders")
            .select("id", "total", "status")
            .where("status = ?", "pending")
            .where("total > ?", 100)
            .order_by("created_at DESC")
            .limit(25)
            .offset(0)
            .fetchall(db)
        )

        # INSERT
        new_id = QueryBuilder("users").insert(db, name="Carol", email="carol@x.com")

        # UPDATE
        QueryBuilder("users").where("id = ?", new_id).update(db, name="Caroline")

        # DELETE
        QueryBuilder("users").where("id = ?", new_id).delete(db)

        # COUNT
        total = QueryBuilder("users").where("active = ?", 1).count(db)
    """

    def __init__(self, table: str) -> None:
        self._table = table
        self._columns: list[str] = ["*"]
        self._conditions: list[str] = []
        self._params: list[Any] = []
        self._order: Optional[str] = None
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
        self._joins: list[str] = []

    # ------------------------------------------------------------------
    # Clause builders
    # ------------------------------------------------------------------

    def select(self, *columns: str) -> "QueryBuilder":
        """Specify columns to return. Defaults to ``*``."""
        self._columns = list(columns)
        return self

    def where(self, condition: str, *params: Any) -> "QueryBuilder":
        """
        Add a WHERE condition.  Multiple calls are AND-ed together.

        ``condition`` should use ``?`` placeholders::

            .where("age > ?", 18)
            .where("active = ?", 1)
        """
        self._conditions.append(condition)
        self._params.extend(params)
        return self

    def join(self, clause: str) -> "QueryBuilder":
        """
        Add a raw JOIN clause, e.g. ``"INNER JOIN tags ON tags.id = posts.tag_id"``.
        """
        self._joins.append(clause)
        return self

    def order_by(self, clause: str) -> "QueryBuilder":
        """Set ORDER BY clause, e.g. ``"created_at DESC"``."""
        self._order = clause
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._limit_val = n
        return self

    def offset(self, n: int) -> "QueryBuilder":
        self._offset_val = n
        return self

    # ------------------------------------------------------------------
    # SQL builders (internal)
    # ------------------------------------------------------------------

    def _build_select(self) -> tuple[str, tuple[Any, ...]]:
        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._joins:
            sql += " " + " ".join(self._joins)
        if self._conditions:
            sql += " WHERE " + " AND ".join(self._conditions)
        if self._order:
            sql += f" ORDER BY {self._order}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        if self._offset_val is not None:
            sql += f" OFFSET {self._offset_val}"
        return sql, tuple(self._params)

    def _build_where_clause(self) -> tuple[str, tuple[Any, ...]]:
        if not self._conditions:
            return "", ()
        return " WHERE " + " AND ".join(self._conditions), tuple(self._params)

    # ------------------------------------------------------------------
    # Terminal methods — execute and return results
    # ------------------------------------------------------------------

    def fetchall(self, db: Database) -> list[sqlite3.Row]:
        """Execute SELECT and return all matching rows."""
        sql, params = self._build_select()
        logger.debug("fetchall: %s | params=%s", sql, params)
        return db.fetchall(sql, params)

    def fetchone(self, db: Database) -> Optional[sqlite3.Row]:
        """Execute SELECT LIMIT 1 and return the first row or ``None``."""
        self._limit_val = 1
        sql, params = self._build_select()
        logger.debug("fetchone: %s | params=%s", sql, params)
        return db.fetchone(sql, params)

    def count(self, db: Database) -> int:
        """Return the number of rows matching the current WHERE clauses."""
        where, params = self._build_where_clause()
        sql = f"SELECT COUNT(*) FROM {self._table}{where}"
        return db.scalar(sql, params) or 0

    def exists(self, db: Database) -> bool:
        """Return ``True`` if at least one row matches."""
        return self.count(db) > 0

    def insert(self, db: Database, **values: Any) -> int | None:
        """
        INSERT a single row.  Keyword arguments map to column names.
        Returns the new row's ``lastrowid``.

        Example::

            new_id = QueryBuilder("users").insert(db, name="Dave", email="d@x.com")
        """
        if not values:
            raise ValueError("insert() requires at least one column=value pair")
        cols = ", ".join(values.keys())
        placeholders = ", ".join("?" * len(values))
        sql = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders});"
        logger.debug("insert: %s | params=%s", sql, tuple(values.values()))
        with db.transaction() as cur:
            cur.execute(sql, tuple(values.values()))
            return cur.lastrowid

    def insert_many(self, db: Database, rows: list[dict[str, Any]]) -> int:
        """
        Bulk INSERT.  All dicts must have identical keys.
        Returns the number of inserted rows.

        Example::

            QueryBuilder("tags").insert_many(db, [{"name": "python"}, {"name": "sqlite"}])
        """
        if not rows:
            return 0
        cols = ", ".join(rows[0].keys())
        placeholders = ", ".join("?" * len(rows[0]))
        sql = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders});"
        data = [tuple(r.values()) for r in rows]
        logger.debug("insert_many: %s | %d rows", sql, len(data))
        with db.transaction() as cur:
            cur.executemany(sql, data)
            return cur.rowcount

    def update(self, db: Database, **values: Any) -> int:
        """
        UPDATE rows matching the current WHERE clauses.
        Returns the number of affected rows.

        Example::

            QueryBuilder("users").where("id = ?", 42).update(db, name="Eve")
        """
        if not values:
            raise ValueError("update() requires at least one column=value pair")
        set_clause = ", ".join(f"{k} = ?" for k in values.keys())
        where, where_params = self._build_where_clause()
        sql = f"UPDATE {self._table} SET {set_clause}{where};"
        params = tuple(values.values()) + where_params
        logger.debug("update: %s | params=%s", sql, params)
        with db.transaction() as cur:
            cur.execute(sql, params)
            return cur.rowcount

    def delete(self, db: Database) -> int:
        """
        DELETE rows matching the current WHERE clauses.
        Returns the number of deleted rows.

        Safety: raises ``RuntimeError`` if no WHERE clause is set (prevents
        accidental full-table deletes). Pass ``unsafe=True`` on the instance
        if you genuinely need a full delete.

        Example::

            QueryBuilder("users").where("active = ?", 0).delete(db)
        """
        where, params = self._build_where_clause()
        if not where:
            raise RuntimeError(
                "delete() without a WHERE clause would wipe the entire table. "
                "Add .where(...) or use db.transaction() directly."
            )
        sql = f"DELETE FROM {self._table}{where};"
        logger.debug("delete: %s | params=%s", sql, params)
        with db.transaction() as cur:
            cur.execute(sql, params)
            return cur.rowcount

    def __repr__(self) -> str:
        sql, params = self._build_select()
        return f"<QueryBuilder sql={sql!r} params={params}>"


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

def get_db(path: str | Path = "app.db") -> Database:
    """
    Return the connected Database singleton.

    Call this from anywhere in your application::

        from db import get_db, QueryBuilder
        db = get_db()
    """
    db = Database(Path(path))
    _ = db.conn  # triggers migration on first call
    return db
