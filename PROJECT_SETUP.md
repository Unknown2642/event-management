# Event Ticketing System - Setup Guide

## 📋 Project Overview
A comprehensive web application for event ticketing similar to BookMyShow, built with Flask framework using Excel files as backend database.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.7+ installed
- Web browser (Chrome, Firefox, Edge)

### 2. Installation Steps
```bash
# 1. Extract the project files
# 2. Navigate to project directory
cd event-ticketing

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py

# 5. Open browser and go to:
http://localhost:5005
```

## 👥 Default User Accounts

| Role | Email | Password | Access Level |
|------|-------|----------|--------------|
| Admin | admin@example.com | admin123 | Full system access |
| Organizer | organizer@example.com | organizer123 | Event management |
| User | user@example.com | user123 | Booking only |

## 🏗️ Project Structure
```
event-ticketing/
├── app.py                     # Main Flask application
├── excel_db.py               # Database operations (Excel)
├── requirements.txt           # Python dependencies
├── run.bat                    # Windows batch file to start app
├── reset_to_defaults.py       # Reset database to default state
├── test_lockout.py           # Login attempt testing
├── PROJECT_SETUP.md          # This setup guide
├── FEATURES.md               # Detailed features documentation
├── data/                     # Excel database files (auto-created)
│   ├── users.xlsx
│   ├── events.xlsx
│   ├── bookings.xlsx
│   ├── venues.xlsx
│   └── feedback.xlsx
├── templates/                # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── organizer_dashboard.html
│   ├── user_dashboard.html
│   ├── events.html
│   ├── book_event.html
│   ├── checkout.html
│   ├── create_event.html
│   ├── edit_event.html
│   └── event_attendees.html
└── uploads/                  # File upload directory (auto-created)
```

## 🔧 Configuration

### Port Configuration
- Default port: `5005`
- To change port, modify `app.py` line: `app.run(debug=True, port=5005)`

### Database Reset
```bash
# Reset all data to defaults (removes custom users/events/bookings)
python reset_to_defaults.py
```

## 🌟 Key Features

### Multi-Role System
- **Admin**: Full system control, user management, event oversight
- **Organizer**: Create/manage events, view attendees, export reports
- **User**: Browse events, book tickets, manage bookings

### Security Features
- Rate limiting (5 requests per minute per API)
- Failed login attempt tracking
- CSRF protection on most endpoints
- Security headers implementation
- Input validation and sanitization

### Intentional Vulnerabilities (For Security Testing)
- **Clickjacking**: Events page can be framed
- **XSS**: Search functionality vulnerable to reflected XSS
- **CSRF**: Some endpoints bypass CSRF protection
- **Insecure Cookies**: Plain text credential storage
- **Open Redirect**: Registration page redirect parameter

### Advanced Features
- **Dynamic Pricing**: 50% price increase for events within 7 days
- **Coupon System**: SAVE10 (10%), SAVE20 (20%), EARLY50 (50%)
- **Real-time Updates**: Seat availability updates
- **Export Reports**: Event and booking data export
- **Responsive Design**: Mobile-friendly interface

## 🔌 API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/register` - User registration
- `POST /api/jwt_login` - JWT authentication

### Events
- `GET /api/events` - List all events
- `POST /api/events` - Create new event (organizer/admin)
- `PUT /api/events/{id}` - Update event
- `DELETE /api/events/{id}` - Delete event

### Bookings
- `POST /api/bookings` - Create booking
- `GET /api/bookings` - Get user bookings
- `POST /api/bookings/{id}/cancel` - Cancel booking

### Special APIs
- `POST /api/soap/validate_coupon` - SOAP-style coupon validation
- `GET /api/dynamic_price/{event_id}` - Get dynamic pricing
- `GET /api/export_reports` - Export data (organizer/admin)

## 🛠️ Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Kill process using port 5005
netstat -ano | findstr :5005
taskkill /PID <process_id> /F
```

**2. Permission Denied (Excel Files)**
- Close Excel if any .xlsx files are open
- Restart the application

**3. Module Not Found**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**4. Database Corruption**
```bash
# Reset to defaults
python reset_to_defaults.py
```

## 🧪 Testing

### Manual Testing
1. **Registration**: Create new user accounts
2. **Login**: Test with different roles
3. **Event Creation**: Create events as organizer
4. **Booking Flow**: Complete ticket booking process
5. **Admin Functions**: Test user/event management
6. **Security Testing**: Test intentional vulnerabilities

### Automated Testing
```bash
# Test login attempt tracking (requires running app)
python test_lockout.py
```

## 📊 Database Schema

### Users Table
- UserID, Name, Email, Role, PasswordHash, FailedAttempts, IsLocked

### Events Table
- EventID, Title, Category, Date, Venue, OrganizerID, TotalSeats, AvailableSeats, Price

### Bookings Table
- BookingID, UserID, EventID, SeatsBooked, BookingDate, Status, Amount, CardLast4

### Venues Table
- VenueID, Name, City, Capacity

### Feedback Table
- FeedbackID, UserID, EventID, Rating, Comments

## 🔒 Security Notes

### For Production Use
1. Change default passwords
2. Enable HTTPS
3. Configure proper CORS origins
4. Remove intentional vulnerabilities
5. Add proper session management
6. Implement proper database (PostgreSQL/MySQL)

### For Security Testing
- Use intentional vulnerabilities responsibly
- Test only on systems you own
- Document findings for educational purposes

## 📞 Support

### Common Commands
```bash
# Start application
python app.py

# Install dependencies
pip install -r requirements.txt

# Reset database
python reset_to_defaults.py

# Test functionality
python test_lockout.py
```

### File Permissions
- Ensure write permissions for `/data` directory
- Ensure write permissions for `/uploads` directory

## 🎯 Next Steps
1. Start the application: `python app.py`
2. Open browser: `http://localhost:5005`
3. Login as admin: `admin@example.com / admin123`
4. Explore the features and functionality
5. Create test events and bookings
6. Test security vulnerabilities (responsibly)

---
**Note**: This is an educational project with intentional security vulnerabilities. Use responsibly and only for learning purposes.