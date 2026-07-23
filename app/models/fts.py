"""Full-text search schema (SQLite FTS5).

SQLAlchemy's declarative models cannot express virtual tables, so the FTS5
table and its synchronization trigger are created with explicit DDL at
startup, alongside Base.metadata.create_all.

Only an INSERT trigger exists: the domain has no update or delete use case,
so triggers for operations that never happen would be dead code.
"""

from sqlalchemy import Engine, text

# Virtual table indexing message content. `content_rowid` links each FTS row
# to the messages table primary key, so search results map back to messages.
_CREATE_FTS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content='messages',
    content_rowid='id'
)
"""

# Keep the index in sync when a message is inserted.
_CREATE_INSERT_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS messages_fts_insert
AFTER INSERT ON messages
BEGIN
    INSERT INTO messages_fts (rowid, content) VALUES (new.id, new.content);
END
"""


def create_fts_schema(engine: Engine) -> None:
    """Create the FTS5 table and its insert trigger if they do not exist."""
    with engine.begin() as conn:
        conn.execute(text(_CREATE_FTS_TABLE))
        conn.execute(text(_CREATE_INSERT_TRIGGER))
