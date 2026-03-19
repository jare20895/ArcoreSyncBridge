"""
CDC Performance Diagnostics Script

Analyzes replication slots and CDC performance to identify issues causing high CPU/IO:
- Inactive slots preventing WAL cleanup (causes disk bloat and high I/O)
- Slot lag (how far behind consumers are)
- WAL size impact
- Missing or orphaned slots
"""
import sys
import os
import psycopg2
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.models.core import DatabaseInstance

def get_db_session():
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def bytes_to_mb(bytes_val):
    """Convert bytes to MB for readability."""
    if bytes_val is None:
        return "N/A"
    return f"{bytes_val / (1024 * 1024):.2f} MB"

def diagnose_cdc_performance():
    print("=" * 80)
    print("CDC PERFORMANCE DIAGNOSTICS")
    print("=" * 80)
    print()

    db = get_db_session()

    # Get all configured instances
    instances = db.execute(
        select(DatabaseInstance).where(DatabaseInstance.replication_slot_name.isnot(None))
    ).scalars().all()

    print(f"Found {len(instances)} instances with configured replication slots.\n")

    # Connect to Postgres
    dsn = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    conn = psycopg2.connect(dsn)
    conn.autocommit = True

    issues_found = []

    try:
        with conn.cursor() as cur:
            # 1. Check overall WAL status
            print("━" * 80)
            print("1. WAL (Write-Ahead Log) Status")
            print("━" * 80)

            cur.execute("""
                SELECT
                    pg_current_wal_lsn() as current_lsn,
                    pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') as wal_position_bytes
            """)
            wal_info = cur.fetchone()
            print(f"Current WAL LSN: {wal_info[0]}")
            print(f"WAL Position: {bytes_to_mb(wal_info[1])}")
            print()

            # 2. Check pg_wal directory size
            print("━" * 80)
            print("2. WAL Directory Size (potential bloat indicator)")
            print("━" * 80)

            cur.execute("""
                SELECT pg_size_pretty(SUM(size)) as wal_size
                FROM pg_ls_waldir()
            """)
            wal_dir_size = cur.fetchone()
            print(f"pg_wal directory size: {wal_dir_size[0]}")
            print("⚠️  If this is > 1GB, there may be slot lag preventing WAL cleanup")
            print()

            # 3. Check all replication slots
            print("━" * 80)
            print("3. Replication Slot Analysis")
            print("━" * 80)

            cur.execute("""
                SELECT
                    slot_name,
                    slot_type,
                    database,
                    active,
                    restart_lsn,
                    confirmed_flush_lsn,
                    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as lag_bytes,
                    pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn) as flush_lag_bytes
                FROM pg_replication_slots
                ORDER BY lag_bytes DESC NULLS LAST
            """)

            slots = cur.fetchall()

            if not slots:
                print("✓ No replication slots found")
            else:
                for slot in slots:
                    slot_name, slot_type, database, active, restart_lsn, flush_lsn, lag_bytes, flush_lag_bytes = slot

                    print(f"\nSlot: {slot_name}")
                    print(f"  Type: {slot_type}")
                    print(f"  Database: {database}")
                    print(f"  Active: {'✓ YES' if active else '✗ NO (INACTIVE!)'}")
                    print(f"  Restart LSN: {restart_lsn}")
                    print(f"  Confirmed Flush LSN: {flush_lsn}")
                    print(f"  Lag: {bytes_to_mb(lag_bytes)}")
                    print(f"  Flush Lag: {bytes_to_mb(flush_lag_bytes)}")

                    # Identify issues
                    if not active:
                        issue = f"⚠️  INACTIVE SLOT: '{slot_name}' - Preventing WAL cleanup!"
                        print(f"  {issue}")
                        issues_found.append(issue)

                    if lag_bytes and lag_bytes > 100 * 1024 * 1024:  # > 100MB
                        issue = f"⚠️  HIGH LAG: '{slot_name}' - {bytes_to_mb(lag_bytes)} behind"
                        print(f"  {issue}")
                        issues_found.append(issue)

            print()

            # 4. Check for configured slots that don't exist
            print("━" * 80)
            print("4. Configuration vs Reality Check")
            print("━" * 80)

            existing_slot_names = {slot[0] for slot in slots}

            for instance in instances:
                slot_name = instance.replication_slot_name
                exists = slot_name in existing_slot_names

                print(f"\nInstance: {instance.instance_label}")
                print(f"  Configured Slot: {slot_name}")
                print(f"  Exists in DB: {'✓ YES' if exists else '✗ NO (MISSING!)'}")

                if not exists:
                    issue = f"⚠️  MISSING SLOT: '{slot_name}' configured for instance '{instance.instance_label}' but not found in database"
                    print(f"  {issue}")
                    issues_found.append(issue)

            print()

            # 5. Check database connections and activity
            print("━" * 80)
            print("5. Database Activity Analysis")
            print("━" * 80)

            cur.execute("""
                SELECT
                    COUNT(*) as total_connections,
                    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                    COUNT(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)

            conn_stats = cur.fetchone()
            print(f"Total Connections: {conn_stats[0]}")
            print(f"Active Connections: {conn_stats[1]}")
            print(f"Idle Connections: {conn_stats[2]}")
            print(f"Waiting Connections: {conn_stats[3]}")

            if conn_stats[1] > 50:
                issue = f"⚠️  HIGH ACTIVE CONNECTIONS: {conn_stats[1]} active connections may be causing CPU load"
                print(f"\n{issue}")
                issues_found.append(issue)

            print()

            # 6. Check for long-running queries
            print("━" * 80)
            print("6. Long-Running Queries (potential CPU hogs)")
            print("━" * 80)

            cur.execute("""
                SELECT
                    pid,
                    usename,
                    application_name,
                    state,
                    EXTRACT(EPOCH FROM (now() - query_start)) as duration_seconds,
                    LEFT(query, 100) as query_preview
                FROM pg_stat_activity
                WHERE state != 'idle'
                  AND query NOT LIKE '%pg_stat_activity%'
                  AND datname = current_database()
                ORDER BY duration_seconds DESC
                LIMIT 10
            """)

            long_queries = cur.fetchall()

            if not long_queries:
                print("✓ No long-running queries")
            else:
                for q in long_queries:
                    pid, user, app, state, duration, query = q
                    print(f"\nPID {pid}: {user} via {app}")
                    print(f"  State: {state}")
                    print(f"  Duration: {duration:.2f}s")
                    print(f"  Query: {query}...")

                    if duration > 10:
                        issue = f"⚠️  SLOW QUERY: PID {pid} running for {duration:.2f}s"
                        issues_found.append(issue)

            print()

            # 7. Check table sizes and bloat potential
            print("━" * 80)
            print("7. Largest Tables (potential optimization targets)")
            print("━" * 80)

            cur.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    n_tup_ins + n_tup_upd + n_tup_del as total_modifications
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)

            tables = cur.fetchall()
            for table in tables:
                schema, name, size, mods = table
                print(f"{schema}.{name}: {size} ({mods:,} modifications)")

            print()

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if issues_found:
        print(f"\n❌ Found {len(issues_found)} issue(s):\n")
        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. {issue}")

        print("\n" + "=" * 80)
        print("RECOMMENDED ACTIONS")
        print("=" * 80)

        for issue in issues_found:
            if "INACTIVE SLOT" in issue:
                print("\n• INACTIVE SLOTS:")
                print("  - Drop unused slots: SELECT pg_drop_replication_slot('<slot_name>');")
                print("  - Or restart the CDC consumer to reactivate")
            elif "HIGH LAG" in issue:
                print("\n• HIGH LAG:")
                print("  - Check if CDC consumer is running: docker-compose ps cdc_consumer")
                print("  - Check consumer logs: docker-compose logs cdc_consumer")
                print("  - May need to increase consumer throughput or add workers")
            elif "MISSING SLOT" in issue:
                print("\n• MISSING SLOTS:")
                print("  - Run: python scripts/inspect_and_fix_slots.py")
                print("  - Or recreate manually via CDC toggle in UI")
            elif "HIGH ACTIVE CONNECTIONS" in issue:
                print("\n• HIGH CONNECTIONS:")
                print("  - Review connection pooling settings")
                print("  - Check for connection leaks in application code")
                print("  - Consider using PgBouncer connection pooler")
            elif "SLOW QUERY" in issue:
                print("\n• SLOW QUERIES:")
                print("  - Review query performance and add indexes")
                print("  - Use EXPLAIN ANALYZE to identify bottlenecks")
                print("  - Consider query optimization or caching")
    else:
        print("\n✓ No major issues detected!")

    print("\n" + "=" * 80)
    print("PERFORMANCE TIPS")
    print("=" * 80)
    print("""
1. Keep replication slots active - inactive slots prevent WAL cleanup
2. Monitor slot lag - high lag indicates consumer can't keep up
3. Regularly vacuum tables - prevents bloat and improves performance
4. Add indexes on frequently queried columns
5. Use connection pooling (max 20-30 connections typically sufficient)
6. Enable query logging to identify slow queries
7. Consider partitioning large tables
8. Use EXPLAIN ANALYZE to optimize slow queries
    """)

if __name__ == "__main__":
    diagnose_cdc_performance()
