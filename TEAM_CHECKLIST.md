# Team Setup Checklist ✅

## 📦 Required Files (All Included)

### Core Application Files
- ✅ `app.py` - Main Flask application
- ✅ `excel_db.py` - Database operations
- ✅ `requirements.txt` - Python dependencies
- ✅ `run.bat` - Windows startup script

### Documentation
- ✅ `PROJECT_SETUP.md` - Complete setup guide
- ✅ `FEATURES.md` - Detailed features documentation
- ✅ `TEAM_CHECKLIST.md` - This checklist
- ✅ `README.md` - Project overview

### Templates (HTML Files)
- ✅ `templates/base.html` - Base template
- ✅ `templates/home.html` - Homepage
- ✅ `templates/login.html` - Login page
- ✅ `templates/register.html` - Registration page
- ✅ `templates/admin_dashboard.html` - Admin interface
- ✅ `templates/organizer_dashboard.html` - Organizer interface
- ✅ `templates/user_dashboard.html` - User interface
- ✅ `templates/events.html` - Event listing
- ✅ `templates/book_event.html` - Booking page
- ✅ `templates/checkout.html` - Payment page
- ✅ `templates/create_event.html` - Event creation
- ✅ `templates/edit_event.html` - Event editing
- ✅ `templates/event_attendees.html` - Attendee list
- ✅ `templates/forgot_password.html` - Password reset
- ✅ `templates/reset_password.html` - Password reset form

### Utility Files
- ✅ `reset_to_defaults.py` - Database reset tool
- ✅ `reset_data.py` - Alternative reset method
- ✅ `test_lockout.py` - Testing script

### Auto-Created Directories
- 📁 `data/` - Excel database files (created on first run)
- 📁 `uploads/` - File upload directory (created on first run)

## 🚀 Quick Start for Team Members

### Option 1: Windows Users (Easiest)
1. Extract all files to a folder
2. Double-click `run.bat`
3. Wait for installation and startup
4. Open browser to `http://localhost:5005`

### Option 2: Manual Setup
```bash
# 1. Navigate to project folder
cd event-ticketing

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start application
python app.py

# 4. Open browser
# Go to: http://localhost:5005
```

## 👥 Test Accounts (Ready to Use)

| Role | Email | Password | Purpose |
|------|-------|----------|---------|
| Admin | admin@example.com | admin123 | Full system access |
| Organizer | organizer@example.com | organizer123 | Event management |
| User | user@example.com | user123 | Booking tickets |

## ✅ Team Testing Checklist

### Basic Functionality
- [ ] Application starts without errors
- [ ] Homepage loads correctly
- [ ] Login with all three default accounts
- [ ] Registration creates new users
- [ ] Admin can see all dashboards

### Event Management
- [ ] Organizer can create events
- [ ] Admin can delete any event
- [ ] Events show dynamic pricing (within 7 days = +50%)
- [ ] Event editing works properly

### Booking System
- [ ] Users can book tickets
- [ ] Payment form validates credit cards
- [ ] Coupons work (SAVE10, SAVE20, EARLY50)
- [ ] Booking confirmation generates ID
- [ ] Users can cancel bookings

### Security Features
- [ ] Rate limiting works (5 requests/minute)
- [ ] Failed login attempts show count
- [ ] CSRF protection on forms
- [ ] XSS vulnerability in search (intentional)
- [ ] Clickjacking on events page (intentional)

### Admin Functions
- [ ] Admin can delete users (except defaults)
- [ ] Admin can delete events (except defaults)
- [ ] Admin dashboard shows all data
- [ ] Export reports functionality

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

**1. "Module not found" error**
```bash
pip install -r requirements.txt --force-reinstall
```

**2. "Port 5005 already in use"**
```bash
# Kill existing process
netstat -ano | findstr :5005
taskkill /PID <process_id> /F
```

**3. "Permission denied" on Excel files**
- Close Excel application if open
- Restart the Flask app

**4. Database corruption**
```bash
python reset_to_defaults.py
```

**5. Application won't start**
- Check Python version: `python --version` (need 3.7+)
- Verify all files are present
- Check file permissions

## 📋 Testing Scenarios

### Scenario 1: Admin Workflow
1. Login as admin@example.com
2. Create a new user via registration
3. Delete the new user from admin dashboard
4. Create a new event
5. Delete the event completely

### Scenario 2: Organizer Workflow
1. Login as organizer@example.com
2. Create multiple events
3. View event attendees
4. Export event reports
5. Edit event details

### Scenario 3: User Workflow
1. Register new user account
2. Browse available events
3. Book tickets with payment
4. Apply coupon codes
5. Cancel a booking

### Scenario 4: Security Testing
1. Test XSS in search: `<script>alert('XSS')</script>`
2. Test rate limiting: Make 6+ API calls quickly
3. Test CSRF on vulnerable endpoints
4. Test clickjacking on events page
5. Check failed login attempt tracking

## 📊 Expected Behavior

### Rate Limiting
- 5 API requests per minute per IP
- Login attempts: 5 per minute per email
- Coupon validation: 3 per minute per user

### Dynamic Pricing
- Events within 7 days: +50% price increase
- Shows "Price Increased" indicator
- Applies to all booking calculations

### Security Vulnerabilities (Intentional)
- Events page: Can be embedded in iframe
- Search: Reflects unescaped input
- Some APIs: No CSRF protection
- Cookies: Store plain text credentials
- Registration: Open redirect vulnerability

## 🎯 Success Criteria

Your setup is successful if:
- ✅ Application starts on `http://localhost:5005`
- ✅ All three user roles can login
- ✅ Events can be created and booked
- ✅ Admin can manage users and events
- ✅ Rate limiting prevents abuse
- ✅ Security vulnerabilities are demonstrable

## 📞 Support

If team members encounter issues:
1. Check this checklist first
2. Review `PROJECT_SETUP.md` for detailed instructions
3. Try the troubleshooting steps above
4. Reset database if needed: `python reset_to_defaults.py`

## 🎓 Learning Objectives

After setup, team should understand:
- Multi-role web application architecture
- Security vulnerability identification
- Rate limiting implementation
- CSRF protection mechanisms
- Input validation importance
- Database operations with Excel backend

---
**Ready to share! All necessary files included for complete project setup.**