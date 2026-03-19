import psycopg2
import os

def check_config():
    dsn = "postgresql://arcore_user:arcore_pass_2024@192.168.1.248:15441/arcore_pm"
    print(f"Connecting to {dsn}...")
    
    try:
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        
        # Check WAL level
        cur.execute("SHOW wal_level")
        print(f"wal_level: {cur.fetchone()[0]}")
        
        # Check current user roles
        cur.execute("SELECT current_user, r.rolsuper, r.rolreplication FROM pg_roles r WHERE r.rolname = current_user")
        row = cur.fetchone()
        print(f"User: {row[0]} | Superuser: {row[1]} | Replication: {row[2]}")
        
        # Check Publication again
        cur.execute("SELECT pubname, puballtables FROM pg_publication WHERE pubname = 'arcore_cdc_pub'")
        row = cur.fetchone()
        if row:
             print(f"Publication Found: {row[0]} | AllTables: {row[1]}")
        else:
             print("Publication NOT found (via this user).")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_config()
