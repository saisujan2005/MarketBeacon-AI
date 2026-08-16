"""
P0 hardening migration.

Applies the schema changes required by the P0 security/scalability fixes.

This project does not use Alembic. Rather than introducing a migration framework
in a hardening pass, this follows the existing convention in app/scripts/:
idempotent DDL, safe to run repeatedly, executed once at startup.

WHAT THIS CHANGES
-----------------
1. posts.alerts_processed_at        (NEW nullable TIMESTAMP)
   Lets alert generation process only new posts instead of rescanning history.
   Backfilled to NOW() for posts that already have alerts, so existing articles
   are not re-alerted on first run after deploy.

2. research_reports.user_id         (NEW nullable UUID + FK + index)
   Gives research reports an owner. Left NULLABLE on purpose: pre-existing rows
   have no known owner, and the retrieval layer requires an exact user_id match,
   so those legacy rows are simply never returned to anybody.

3. alerts.importance_score          (TYPE String -> Integer)
   Converted with a USING clause that tolerates non-numeric legacy values
   (they become NULL). Needed because ">= 80" was comparing text.

4. Indexes on posts / alerts / notifications / watchlists / holdings.
   All CREATE INDEX IF NOT EXISTS.

5. company_peer_caches.company_name        (UNIQUE index -> plain index)
   A stale globally-unique index made the peer cache single-tenant: once one
   user cached "HDFC Bank", any other user caching the same company hit
   "duplicate key value violates unique constraint", peer/sector discovery
   failed for them, and their watchlist entry fell back to guessed metadata.
   The intended uniqueness, (user_id, company_name), already exists separately
   as uq_user_company_peer and is left untouched.

WHAT THIS DOES *NOT* DO
-----------------------
No table is dropped. No row is deleted. No column is dropped. No data is reset.
The only destructive-looking operation is the importance_score type change,
which preserves every numeric value.
"""

import logging

from sqlalchemy import inspect, text

from app.db.database import engine

logger = logging.getLogger(__name__)


# (index_name, table, columns) -- all additive, all IF NOT EXISTS.
INDEXES = [
    # posts: the largest, hottest table; previously had no indexes at all.
    ("ix_posts_posted_at",           "posts",         "(posted_at)"),
    ("ix_posts_importance_score",    "posts",         "(importance_score)"),
    ("ix_posts_event_type",          "posts",         "(event_type)"),
    ("ix_posts_source_id",           "posts",         "(source_id)"),
    ("ix_posts_title",               "posts",         "(title)"),
    ("ix_posts_post_url",            "posts",         "(post_url)"),
    ("ix_posts_alerts_processed_at", "posts",         "(alerts_processed_at)"),
    # /market-summary: WHERE importance_score >= 70 ORDER BY posted_at DESC
    ("ix_posts_importance_posted",   "posts",         "(importance_score, posted_at)"),
    # alert queue scan: WHERE alerts_processed_at IS NULL AND importance_score IS NOT NULL
    ("ix_posts_alertqueue",          "posts",         "(alerts_processed_at, importance_score)"),

    # user-scoped tables: every query filters on user_id.
    ("ix_alerts_user_id",            "alerts",        "(user_id)"),
    ("ix_alerts_user_created",       "alerts",        "(user_id, created_at)"),
    ("ix_alerts_user_post",          "alerts",        "(user_id, post_id)"),
    ("ix_alerts_post_id",            "alerts",        "(post_id)"),

    ("ix_notifications_user_id",      "notifications", "(user_id)"),
    ("ix_notifications_user_created", "notifications", "(user_id, created_at)"),
    ("ix_notifications_user_keyword", "notifications", "(user_id, keyword)"),

    ("ix_watchlists_user_id",        "watchlists",    "(user_id)"),
    ("ix_watchlists_user_company",   "watchlists",    "(user_id, company_name)"),

    ("ix_holdings_user_id",          "holdings",      "(user_id)"),
    ("ix_holdings_user_company",     "holdings",      "(user_id, company_name)"),

    ("ix_research_reports_user_id",  "research_reports", "(user_id)"),
    ("ix_research_reports_user_entity_created",
     "research_reports", "(user_id, entity_name, created_at)"),
]


def _table_exists(inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def _column_exists(inspector, table: str, column: str) -> bool:
    try:
        return column in [c["name"] for c in inspector.get_columns(table)]
    except Exception:
        return False


def _column_type(inspector, table: str, column: str) -> str:
    for c in inspector.get_columns(table):
        if c["name"] == column:
            return str(c["type"]).upper()
    return ""


def upgrade_p0_hardening() -> None:
    logger.info("[P0 migration] Starting hardening schema migration...")
    inspector = inspect(engine)

    # ── 1. posts.alerts_processed_at ────────────────────────────────────────
    if _table_exists(inspector, "posts"):
        if not _column_exists(inspector, "posts", "alerts_processed_at"):
            logger.info("[P0 migration] Adding posts.alerts_processed_at ...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text(
                        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS alerts_processed_at TIMESTAMP;"
                    ))
                    # Mark posts that already produced alerts as processed, so the
                    # new incremental pipeline does not re-alert historical news.
                    conn.execute(text("""
                        UPDATE posts
                           SET alerts_processed_at = NOW()
                         WHERE alerts_processed_at IS NULL
                           AND (
                                 id IN (SELECT post_id FROM alerts WHERE post_id IS NOT NULL)
                              OR title IN (SELECT title FROM alerts WHERE title IS NOT NULL)
                               );
                    """))
            logger.info("[P0 migration] posts.alerts_processed_at added and backfilled.")
        else:
            logger.info("[P0 migration] posts.alerts_processed_at already present.")

    # ── 2. research_reports.user_id ─────────────────────────────────────────
    if _table_exists(inspector, "research_reports"):
        if not _column_exists(inspector, "research_reports", "user_id"):
            logger.info("[P0 migration] Adding research_reports.user_id ...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text(
                        "ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS user_id UUID;"
                    ))
                    conn.execute(text("""
                        ALTER TABLE research_reports
                        ADD CONSTRAINT fk_research_reports_user_id
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                    """))
            logger.info(
                "[P0 migration] research_reports.user_id added. Pre-existing rows keep "
                "user_id = NULL and are excluded from all retrieval."
            )
        else:
            logger.info("[P0 migration] research_reports.user_id already present.")

    # ── 3. alerts.importance_score -> INTEGER ───────────────────────────────
    if _table_exists(inspector, "alerts") and _column_exists(inspector, "alerts", "importance_score"):
        col_type = _column_type(inspector, "alerts", "importance_score")
        if "INT" not in col_type:
            logger.info(
                "[P0 migration] Converting alerts.importance_score from %s to INTEGER ...",
                col_type or "UNKNOWN",
            )
            with engine.connect() as conn:
                with conn.begin():
                    # Strips any non-numeric characters; values that cannot be
                    # interpreted become NULL rather than aborting the migration.
                    conn.execute(text("""
                        ALTER TABLE alerts
                        ALTER COLUMN importance_score TYPE INTEGER
                        USING NULLIF(regexp_replace(importance_score::text, '[^0-9-]', '', 'g'), '')::INTEGER;
                    """))
            logger.info("[P0 migration] alerts.importance_score is now INTEGER.")
        else:
            logger.info("[P0 migration] alerts.importance_score already INTEGER.")

    # ── 4. Indexes ──────────────────────────────────────────────────────────
    inspector = inspect(engine)  # refresh after DDL
    created = 0
    for index_name, table, columns in INDEXES:
        if not _table_exists(inspector, table):
            continue
        try:
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text(
                        f'CREATE INDEX IF NOT EXISTS {index_name} ON {table} {columns};'
                    ))
            created += 1
        except Exception as e:
            # An index failure must never prevent the application from starting.
            logger.warning("[P0 migration] Could not create index %s on %s: %s", index_name, table, e)

    logger.info("[P0 migration] Index pass complete (%d/%d verified).", created, len(INDEXES))

    # ── 5. company_peer_caches: drop the stale globally-unique index ────────
    #
    # The model declares company_name as index=True (non-unique); fresh
    # databases are already correct. Older databases carry a UNIQUE variant of
    # ix_company_peer_caches_company_name from an earlier model definition,
    # which prevents two users from caching the same company.
    if _table_exists(inspector, "company_peer_caches"):
        try:
            with engine.connect() as conn:
                with conn.begin():
                    is_unique = conn.execute(text("""
                        SELECT i.indisunique
                          FROM pg_class c
                          JOIN pg_index i ON i.indexrelid = c.oid
                         WHERE c.relname = 'ix_company_peer_caches_company_name'
                    """)).scalar()

                    if is_unique is None:
                        logger.info("[P0 migration] ix_company_peer_caches_company_name absent; creating plain index.")
                        conn.execute(text(
                            "CREATE INDEX IF NOT EXISTS ix_company_peer_caches_company_name "
                            "ON company_peer_caches (company_name);"
                        ))
                    elif is_unique:
                        logger.info(
                            "[P0 migration] ix_company_peer_caches_company_name is UNIQUE "
                            "(blocks multi-user caching); replacing with a plain index..."
                        )
                        # It is a bare index, not a constraint, so DROP INDEX is correct.
                        conn.execute(text("DROP INDEX IF EXISTS ix_company_peer_caches_company_name;"))
                        conn.execute(text(
                            "CREATE INDEX IF NOT EXISTS ix_company_peer_caches_company_name "
                            "ON company_peer_caches (company_name);"
                        ))
                        logger.info("[P0 migration] Replaced with a non-unique index. No rows were touched.")
                    else:
                        logger.info("[P0 migration] ix_company_peer_caches_company_name already non-unique.")

                    # The real per-tenant uniqueness. Additive; never dropped.
                    exists_uq = conn.execute(text("""
                        SELECT 1 FROM pg_constraint con
                          JOIN pg_class rel ON rel.oid = con.conrelid
                         WHERE rel.relname = 'company_peer_caches'
                           AND con.conname = 'uq_user_company_peer'
                    """)).scalar()
                    if not exists_uq:
                        logger.info("[P0 migration] Adding uq_user_company_peer (user_id, company_name)...")
                        conn.execute(text(
                            "ALTER TABLE company_peer_caches "
                            "ADD CONSTRAINT uq_user_company_peer UNIQUE (user_id, company_name);"
                        ))
        except Exception as e:
            logger.warning("[P0 migration] Could not normalise company_peer_caches indexes: %s", e)

    logger.info("[P0 migration] Hardening schema migration finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
    upgrade_p0_hardening()
    print("P0 hardening migration complete.")
