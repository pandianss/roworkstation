from __future__ import annotations
import os
import sys
from src.infrastructure.persistence.database import engine
from src.infrastructure.persistence.sqlite_models import Base

def seed_local_environment():
    """Initializes all SQLite database schema tables on-demand."""
    print("🚀 Regional Operations Cockpit: Persistent Storage Seeder Initializing...")
    try:
        # Create all tables defined in sqlite_models.py
        Base.metadata.create_all(engine)
        print("✅ SQLite database tables and index schemas successfully initialized!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error during database seeder initialization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    seed_local_environment()
