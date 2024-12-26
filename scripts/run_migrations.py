"""Script to run database migrations."""

import os
from db.connection import Database
from db.migrations import MigrationManager

def main():
    """Run database migrations."""
    print("Running database migrations...")
    
    # Get database path from environment or use default
    db_path = os.getenv("DATABASE_URL", "db/github_repos.db")
    print(f"Using database at: {db_path}")
    
    # Connect to main database
    db = Database(db_path)
    db.connect()
    
    try:
        # Initialize and run migrations
        migration_manager = MigrationManager(db)
        migration_manager.apply_migrations()
        print("Migrations completed successfully")
        
    except Exception as e:
        print(f"Error running migrations: {str(e)}")
        raise
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
