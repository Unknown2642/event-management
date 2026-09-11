from excel_db import ExcelDB

def main():
    print("Resetting database to default state...")
    
    # Initialize database
    db = ExcelDB()
    
    # Reset to defaults
    db.reset_to_defaults()
    
    print("Database reset completed!")
    print("\nDefault Data Restored:")
    print("Users:")
    print("   1. Admin User (admin@example.com / admin123)")
    print("   2. Event Organizer (organizer@example.com / organizer123)")
    print("   3. Regular User (user@example.com / user123)")
    
    print("\nEvents:")
    print("   1. Rock Concert - Music - Dec 25, 2024")
    print("   2. Comedy Night - Comedy - Dec 30, 2024")
    print("   3. Tech Conference - Conference - Jan 15, 2025")
    
    print("\nRemoved:")
    print("   - All custom users (ID > 3)")
    print("   - All custom events (ID > 3)")
    print("   - All bookings")
    print("   - All feedback")
    
    print("\nProtected:")
    print("   - Default users (IDs 1-3) cannot be deleted")
    print("   - Default events (IDs 1-3) cannot be deleted/cancelled")

if __name__ == "__main__":
    main()