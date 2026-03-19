import psycopg2
import os

def create_slot():
    dsn = "postgresql://arcore_user:arcore_pass_2024@192.168.1.248:15441/arcore_pm"
    print(f"Connecting to {dsn}...")
    
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Creating slot 'arcorevector_cdc_slot' (pgoutput)...")
        cur.execute("SELECT pg_create_logical_replication_slot('arcorevector_cdc_slot', 'pgoutput')")
        print("Slot created.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_slot()
