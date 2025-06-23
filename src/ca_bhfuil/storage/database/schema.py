"""Database schema definitions for ca-bhfuil."""

import contextlib
import pathlib
import sqlite3
import typing

from loguru import logger

from ca_bhfuil.core import config


class DatabaseManager:
    """SQLite database manager for ca-bhfuil."""

    def __init__(self, db_path: pathlib.Path | None = None) -> None:
        """Initialize database manager.

        Args:
            db_path: Optional database path override
        """
        cache_dir = config.get_cache_dir()
        self.db_path = db_path or (cache_dir / "ca-bhfuil.db")

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.debug(f"Initialized database at {self.db_path}")

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create repositories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    last_analyzed TIMESTAMP,
                    commit_count INTEGER DEFAULT 0,
                    branch_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create commits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id INTEGER NOT NULL,
                    sha TEXT NOT NULL,
                    short_sha TEXT NOT NULL,
                    message TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    author_email TEXT NOT NULL,
                    author_date TIMESTAMP NOT NULL,
                    committer_name TEXT NOT NULL,
                    committer_email TEXT NOT NULL,
                    committer_date TIMESTAMP NOT NULL,
                    files_changed INTEGER,
                    insertions INTEGER,
                    deletions INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (repository_id) REFERENCES repositories (id),
                    UNIQUE (repository_id, sha)
                )
            """)

            # Create branches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS branches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    target_sha TEXT,
                    is_remote BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (repository_id) REFERENCES repositories (id),
                    UNIQUE (repository_id, name)
                )
            """)

            # Create commit_branches junction table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commit_branches (
                    commit_id INTEGER NOT NULL,
                    branch_id INTEGER NOT NULL,
                    PRIMARY KEY (commit_id, branch_id),
                    FOREIGN KEY (commit_id) REFERENCES commits (id),
                    FOREIGN KEY (branch_id) REFERENCES branches (id)
                )
            """)

            # Create indexes for better performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_commits_sha ON commits (sha)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_commits_short_sha ON commits (short_sha)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_commits_author_date ON commits (author_date)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_commits_repository_id ON commits (repository_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_branches_name ON branches (name)"
            )

            conn.commit()

    @contextlib.contextmanager
    def get_connection(self) -> typing.Iterator[sqlite3.Connection]:
        """Get database connection context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()

    def add_repository(self, path: str, name: str) -> int:
        """Add a repository to the database.

        Args:
            path: Repository path
            name: Repository name

        Returns:
            Repository ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO repositories (path, name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (path, name),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_repository(self, path: str) -> dict[str, typing.Any] | None:
        """Get repository by path.

        Args:
            path: Repository path

        Returns:
            Repository data or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM repositories WHERE path = ?", (path,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_repository_stats(
        self, repo_id: int, commit_count: int, branch_count: int
    ) -> None:
        """Update repository statistics.

        Args:
            repo_id: Repository ID
            commit_count: Number of commits
            branch_count: Number of branches
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE repositories
                SET commit_count = ?, branch_count = ?, last_analyzed = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (commit_count, branch_count, repo_id),
            )
            conn.commit()

    def add_commit(self, repository_id: int, commit_data: dict[str, typing.Any]) -> int:
        """Add a commit to the database.

        Args:
            repository_id: Repository ID
            commit_data: Commit information

        Returns:
            Commit ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO commits (
                    repository_id, sha, short_sha, message,
                    author_name, author_email, author_date,
                    committer_name, committer_email, committer_date,
                    files_changed, insertions, deletions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    repository_id,
                    commit_data["sha"],
                    commit_data["short_sha"],
                    commit_data["message"],
                    commit_data["author_name"],
                    commit_data["author_email"],
                    commit_data["author_date"],
                    commit_data["committer_name"],
                    commit_data["committer_email"],
                    commit_data["committer_date"],
                    commit_data.get("files_changed"),
                    commit_data.get("insertions"),
                    commit_data.get("deletions"),
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def find_commits(
        self,
        repository_id: int,
        sha_pattern: str | None = None,
        message_pattern: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, typing.Any]]:
        """Find commits matching criteria.

        Args:
            repository_id: Repository ID
            sha_pattern: SHA pattern to match
            message_pattern: Message pattern to match
            limit: Maximum results

        Returns:
            List of matching commits
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            where_clauses = ["repository_id = ?"]
            params: list[typing.Any] = [repository_id]

            if sha_pattern:
                where_clauses.append("(sha LIKE ? OR short_sha LIKE ?)")
                params.extend([f"%{sha_pattern}%", f"%{sha_pattern}%"])

            if message_pattern:
                where_clauses.append("message LIKE ?")
                params.append(f"%{message_pattern}%")

            query = f"""
                SELECT * FROM commits
                WHERE {" AND ".join(where_clauses)}
                ORDER BY author_date DESC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict[str, typing.Any]:
        """Get database statistics.

        Returns:
            Database statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM repositories")
            repo_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM commits")
            commit_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM branches")
            branch_count = cursor.fetchone()[0]

            return {
                "repositories": repo_count,
                "commits": commit_count,
                "branches": branch_count,
                "database_path": str(self.db_path),
            }


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
