import shutil
import os
from datetime import datetime

def backup_database():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    src = os.path.join(data_dir, "gold_tracker.db")
    
    if not os.path.exists(src):
        print(f"Error: Source database file not found at {src}")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(data_dir, f"gold_tracker_backup_{timestamp}.db")
    
    try:
        shutil.copy2(src, dst)
        print(f"Database backed up successfully to {dst}")
    except Exception as e:
        print(f"Failed to copy database: {e}")

if __name__ == "__main__":
    backup_database()
