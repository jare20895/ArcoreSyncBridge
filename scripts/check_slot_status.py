import sys
import os
import time
import psycopg2

def check_status():
    db_user = os.environ.get("POSTGRES_USER", "change_me")
    db_password = os.environ.get("POSTGRES_PASSWORD", "change_me")
    db_host = os.environ.get("POSTGRES_HOST", "localhost")
    db_port = os.environ.get("POSTGRES_PORT", "5465")
    db_name = os.environ.get("POSTGRES_DB", "arcore_syncbridge")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print(f"Checking slot status on {dsn}...")
    
    try:
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        
        for i in range(10): # Try for 10 seconds
            cur.execute("SELECT slot_name, plugin, active, active_pid FROM pg_replication_slots WHERE slot_name = 'arcorevector_cdc_slot'")
            row = cur.fetchone()
            
            if row:
                print(f"Slot: {row[0]} | Plugin: {row[1]} | Active: {row[2]} | PID: {row[3]}")
                if row[2]: # Active
                    print("[SUCCESS] Slot is ACTIVE.")
                    return
            else:
                print("Slot not found.")
                
            time.sleep(1)
            
        print("[TIMEOUT] Slot did not become active within 10 seconds.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    check_status()
