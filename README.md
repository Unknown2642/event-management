# Event Ticketing System

A minimal web application for event ticketing and management using Excel files as the backend database.

## Features

### User Roles
- **Admin**: Manages users, events, venues, and analytics
- **Organizer**: Creates and manages events, sets ticket pricing and availability
- **User/Attendee**: Browses events, books tickets, and receives confirmations

### Core Functionality
- User registration and login with role-based access
- Event listing with filters (category, city)
- Real-time seat availability check and booking
- Excel-based data storage and retrieval
- Admin dashboard with comprehensive analytics
- Organizer dashboard for event management
- User dashboard for booking history

## Excel Database Structure

The application uses 5 Excel files:

1. **users.xlsx**: UserID, Name, Email, Role, PasswordHash
2. **events.xlsx**: EventID, Title, Category, Date, Venue, OrganizerID, TotalSeats, AvailableSeats, Price
3. **bookings.xlsx**: BookingID, UserID, EventID, SeatsBooked, BookingDate, Status
4. **venues.xlsx**: VenueID, Name, City, Capacity
5. **feedback.xlsx**: FeedbackID, UserID, EventID, Rating, Comments

## Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```
   Or use the batch file:
   ```bash
   run.bat
   ```

3. **Access the Application**
   - Open browser and go to `http://localhost:5005`

## Demo Credentials

- **Admin**: admin@example.com / admin123
- **Organizer**: organizer@example.com / organizer123  
- **User**: user@example.com / user123

## Usage

1. **Register** as a new user (User/Organizer)
2. **Login** with your credentials
3. **Browse Events** on the home page or events page
4. **Book Tickets** by selecting an event and choosing seats
5. **Manage Events** (Organizers can create new events)
6. **Admin Panel** (Admins can view all users, events, and bookings)

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Excel files (pandas + openpyxl)
- **Frontend**: HTML/CSS/JavaScript
- **Authentication**: Session-based with password hashing

## Project Structure

```
event-ticketing/
├── data/                   # Excel database files
├── templates/              # HTML templates
├── static/                 # CSS/JS files (if needed)
├── app.py                 # Main Flask application
├── excel_db.py           # Excel database handler
├── requirements.txt       # Python dependencies
├── run.bat               # Windows run script
└── README.md             # This file
```

## Features Implemented

✅ Multi-role user system (Admin/Organizer/User)
✅ Event creation and management
✅ Real-time ticket booking
✅ Seat availability tracking
✅ Excel-based data persistence
✅ Role-based dashboard access
✅ Event filtering and search
✅ Booking confirmation system
✅ Admin analytics dashboard

## Future Enhancements

- Email notifications for bookings
- Payment integration
- Event feedback system
- Advanced reporting
- Mobile-responsive design
- Event categories management
- Venue management system