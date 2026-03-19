import psycopg2
import os

def drop_slot():
    dsn = "postgresql://arcore_user:arcore_pass_2024@192.168.1.248:15441/arcore_pm"
    print(f"Connecting to {dsn}...")
    
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if exists
        cur.execute("SELECT slot_name, active_pid FROM pg_replication_slots WHERE slot_name = 'arcorevector_cdc_slot'")
        row = cur.fetchone()
        
        if row:
            print(f"Slot found. PID: {row[1]}")
            if row[1]:
                 print("Slot is active. Terminating backend...")
                 cur.execute(f"SELECT pg_terminate_backend({row[1]})")
            
            print("Dropping slot 'arcorevector_cdc_slot'...")
            cur.execute("SELECT pg_drop_replication_slot('arcorevector_cdc_slot')")
            print("Slot dropped.")
        else:
            print("Slot not found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    drop_slot()
