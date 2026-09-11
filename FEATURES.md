# Event Ticketing System - Features Documentation

## 🎯 Core Features

### 1. Multi-Role Authentication System
- **Admin Role**: Complete system control
  - User management (create, delete users)
  - Event oversight (manage all events)
  - Booking management (view all bookings)
  - System configuration access

- **Organizer Role**: Event management focus
  - Create and manage own events
  - View event attendees
  - Export event reports
  - Edit event details

- **User Role**: Customer experience
  - Browse available events
  - Book tickets with payment
  - Manage personal bookings
  - Cancel bookings

### 2. Event Management System
- **Event Creation**: Title, category, date, venue, seats, pricing
- **Dynamic Pricing**: 50% price increase for events within 7 days
- **Seat Management**: Real-time availability tracking
- **Event Categories**: Music, Comedy, Conference, Sports, etc.
- **Venue Integration**: Predefined venues with capacity limits
- **Event Visibility**: Public or organizer-only events

### 3. Advanced Booking System
- **Multi-seat Booking**: Book multiple seats in single transaction
- **Payment Processing**: Credit card validation with Luhn algorithm
- **Coupon System**: 
  - SAVE10 (10% discount)
  - SAVE20 (20% discount)
  - EARLY50 (50% discount)
- **Booking Confirmation**: Unique booking ID generation
- **Cancellation System**: Full refund with seat restoration

### 4. Security Implementation
- **Rate Limiting**: 5 requests per minute per IP for all APIs
- **Login Attempt Tracking**: Shows failed attempt count
- **CSRF Protection**: Implemented on critical endpoints
- **Input Validation**: Comprehensive data sanitization
- **Security Headers**: XSS protection, clickjacking prevention
- **Session Management**: Secure session handling

### 5. Intentional Security Vulnerabilities (For Testing)
- **Clickjacking**: Events page vulnerable to iframe embedding
- **Reflected XSS**: Search functionality lacks input sanitization
- **CSRF Bypass**: Some endpoints intentionally vulnerable
- **Insecure Cookie Storage**: Plain text credentials in cookies
- **Open Redirect**: Registration redirect parameter unvalidated

## 🔧 Technical Features

### 1. Database Architecture
- **Excel-based Storage**: Uses openpyxl for data persistence
- **CRUD Operations**: Complete Create, Read, Update, Delete functionality
- **Data Integrity**: Referential integrity between tables
- **Backup System**: Reset to defaults functionality
- **Random ID Generation**: Events use random IDs (1000-999999)

### 2. API Architecture
- **RESTful APIs**: Standard HTTP methods and status codes
- **SOAP Integration**: Coupon validation via SOAP-style API
- **JWT Support**: Token-based authentication option
- **CORS Configuration**: Cross-origin resource sharing enabled
- **Error Handling**: Comprehensive exception management

### 3. Frontend Features
- **Responsive Design**: Mobile-friendly interface
- **Glassmorphism UI**: Modern visual design
- **Real-time Updates**: Dynamic content loading
- **Form Validation**: Client and server-side validation
- **Interactive Elements**: Confirmation dialogs, loading states

### 4. Advanced Functionality
- **Search & Filter**: Event search with multiple criteria
- **Sorting Options**: Price, date, name-based sorting
- **Export Reports**: CSV/JSON data export for organizers
- **File Upload Support**: Profile pictures and documents
- **Pagination**: Large dataset handling

## 🛡️ Security Features Detail

### 1. Authentication Security
```python
# Login attempt tracking
failed_attempts = session.get('failed_attempts', 0) + 1
session['failed_attempts'] = failed_attempts

# Rate limiting implementation
if is_login_rate_limited(email):
    return "Too many login attempts. Please try again later."
```

### 2. Input Validation
```python
# Email validation
if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
    return "Invalid email format"

# SQL injection prevention
# Using parameterized queries and input sanitization
```

### 3. CSRF Protection
```python
# CSRF token generation
def generate_csrf_token():
    return secrets.token_hex(32)

# CSRF validation
@csrf_required
def protected_endpoint():
    # Endpoint logic here
```

## 🎨 User Interface Features

### 1. Dashboard Interfaces
- **Admin Dashboard**: User management, event oversight, system stats
- **Organizer Dashboard**: Event management, attendee lists, reports
- **User Dashboard**: Booking history, profile management

### 2. Event Browsing
- **Event Listing**: Grid/list view with filtering
- **Event Details**: Comprehensive event information
- **Seat Selection**: Visual seat availability
- **Price Display**: Dynamic pricing with discounts

### 3. Booking Flow
- **Event Selection**: Browse and select events
- **Seat Selection**: Choose number of seats
- **Payment Processing**: Secure payment form
- **Confirmation**: Booking confirmation with details

## 🔌 API Documentation

### Authentication Endpoints
```
POST /api/login
POST /api/register
POST /api/jwt_login
GET /csrf-token
```

### Event Management
```
GET /api/events
POST /api/events
PUT /api/events/{id}
DELETE /api/events/{id}
GET /api/events/{id}/attendees
```

### Booking Operations
```
POST /api/bookings
GET /api/bookings
POST /api/bookings/{id}/cancel
```

### Special Features
```
POST /api/soap/validate_coupon
GET /api/dynamic_price/{event_id}
GET /api/export_reports
```

## 📊 Data Management

### 1. Excel Database Structure
- **users.xlsx**: User accounts and authentication
- **events.xlsx**: Event information and availability
- **bookings.xlsx**: Booking records and payments
- **venues.xlsx**: Venue information and capacity
- **feedback.xlsx**: User feedback and ratings

### 2. Data Relationships
- Users → Bookings (One-to-Many)
- Events → Bookings (One-to-Many)
- Organizers → Events (One-to-Many)
- Venues → Events (One-to-Many)

### 3. Data Protection
- Default data protection (IDs 1-3 cannot be deleted)
- Referential integrity maintenance
- Automatic cleanup on deletions
- Backup and restore functionality

## 🧪 Testing Features

### 1. Automated Testing
- Login attempt tracking tests
- Rate limiting verification
- CSRF protection tests
- Input validation tests

### 2. Security Testing
- XSS vulnerability testing
- CSRF bypass testing
- Clickjacking demonstration
- Open redirect testing

### 3. Performance Testing
- Rate limiting stress tests
- Database operation performance
- Concurrent user handling
- Memory usage monitoring

## 🚀 Deployment Features

### 1. Configuration Management
- Environment-based settings
- Port configuration
- Debug mode toggle
- Database path configuration

### 2. Error Handling
- Comprehensive exception catching
- User-friendly error messages
- Logging and monitoring
- Graceful degradation

### 3. Maintenance Tools
- Database reset functionality
- Data export/import tools
- System health checks
- Performance monitoring

## 📈 Analytics & Reporting

### 1. Event Analytics
- Booking statistics
- Revenue tracking
- Attendance reports
- Popular events analysis

### 2. User Analytics
- Registration trends
- Booking patterns
- User engagement metrics
- Retention analysis

### 3. System Metrics
- API usage statistics
- Error rate monitoring
- Performance metrics
- Security incident tracking

---

## 🎓 Educational Value

This project demonstrates:
- **Web Application Security**: Both secure practices and common vulnerabilities
- **Full-Stack Development**: Frontend, backend, and database integration
- **API Design**: RESTful and SOAP API implementation
- **User Experience**: Multi-role interface design
- **Data Management**: Excel-based database operations
- **Testing Practices**: Automated and manual testing approaches

Perfect for learning web security, full-stack development, and understanding common web application vulnerabilities in a controlled environment.