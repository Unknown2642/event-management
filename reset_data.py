import os
import hashlib
from openpyxl import Workbook

# Delete existing files
data_dir = 'data'
files = ['users.xlsx', 'events.xlsx', 'bookings.xlsx', 'venues.xlsx', 'feedback.xlsx']
for file in files:
    try:
        os.remove(os.path.join(data_dir, file))
        print(f"Deleted {file}")
    except:
        pass

# Create users.xlsx
wb = Workbook()
ws = wb.active
ws.append(['UserID', 'Name', 'Email', 'Role', 'PasswordHash'])
admin_hash = hashlib.sha256('admin123'.encode()).hexdigest()
organizer_hash = hashlib.sha256('organizer123'.encode()).hexdigest()
user_hash = hashlib.sha256('user123'.encode()).hexdigest()
ws.append([1, 'Admin User', 'admin@example.com', 'admin', admin_hash])
ws.append([2, 'Event Organizer', 'organizer@example.com', 'organizer', organizer_hash])
ws.append([3, 'Regular User', 'user@example.com', 'user', user_hash])
wb.save(os.path.join(data_dir, 'users.xlsx'))
print("Created users.xlsx")

# Create events.xlsx
wb = Workbook()
ws = wb.active
ws.append(['EventID', 'Title', 'Category', 'Date', 'Venue', 'OrganizerID', 'TotalSeats', 'AvailableSeats', 'Price'])
ws.append([1, 'Rock Concert', 'Music', '2024-12-25', 'Stadium A', 2, 1000, 950, 50.0])
ws.append([2, 'Comedy Night', 'Comedy', '2024-12-30', 'Theater B', 2, 500, 480, 25.0])
ws.append([3, 'Tech Conference', 'Conference', '2025-01-15', 'Convention Center', 2, 200, 180, 100.0])
wb.save(os.path.join(data_dir, 'events.xlsx'))
print("Created events.xlsx")

# Create empty files
for file in ['bookings.xlsx', 'venues.xlsx', 'feedback.xlsx']:
    wb = Workbook()
    ws = wb.active
    if file == 'bookings.xlsx':
        ws.append(['BookingID', 'UserID', 'EventID', 'SeatsBooked', 'BookingDate', 'Status', 'Amount', 'CardLast4'])
    elif file == 'venues.xlsx':
        ws.append(['VenueID', 'Name', 'City', 'Capacity'])
        ws.append([1, 'Stadium A', 'New York', 1000])
        ws.append([2, 'Theater B', 'Los Angeles', 500])
        ws.append([3, 'Convention Center', 'Chicago', 200])
    else:
        ws.append(['FeedbackID', 'UserID', 'EventID', 'Rating', 'Comments'])
    wb.save(os.path.join(data_dir, file))
    print(f"Created {file}")

print("All files recreated successfully!")