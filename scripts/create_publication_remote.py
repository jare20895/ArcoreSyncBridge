import psycopg2
import os

def create_pub():
    dsn = "postgresql://arcore_user:arcore_pass_2024@192.168.1.248:15441/arcore_pm"
    print(f"Connecting to {dsn}...")
    
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if exists
        cur.execute("SELECT pubname FROM pg_publication WHERE pubname = 'arcore_cdc_pub'")
        if cur.fetchone():
            print("Publication 'arcore_cdc_pub' already exists.")
        else:
            print("Creating publication 'arcore_cdc_pub' for all tables...")
            cur.execute("CREATE PUBLICATION arcore_cdc_pub FOR ALL TABLES")
            print("Publication created.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_pub()
