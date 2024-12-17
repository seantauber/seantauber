"""Script to run database migrations."""

from db.connection import Database
from db.migrations import MigrationManager

def main():
    """Run database migrations."""
    print("Running database migrations...")
    
    # Connect to main database
    db = Database("db/chroma.sqlite3")
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
