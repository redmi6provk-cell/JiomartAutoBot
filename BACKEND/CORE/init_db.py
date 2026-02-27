"""
Initialize database tables for JioMart automation.
Run this script to create all database tables.
"""
import sys
from database import init_db, test_connection

def main():
    print("🔧 Initializing JioMart Database...")
    print("=" * 50)
    
    # Test connection first
    print("\n1️⃣ Testing database connection...")
    if not test_connection():
        print("\n❌ Failed to connect to database!")
        print("Please check:")
        print("  - PostgreSQL is running")
        print("  - Database 'jiomart' exists")
        print("  - Username and password are correct")
        sys.exit(1)
    
    # Create tables
    print("\n2️⃣ Creating database tables...")
    try:
        init_db()
        print("\n✅ Database initialization complete!")
        print("\nTables created:")
        print("  - profiles")
        print("  - cookies")
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
