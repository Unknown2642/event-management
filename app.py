from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS, cross_origin
from excel_db import ExcelDB
from datetime import datetime, timedelta
import time
from collections import defaultdict
import jwt
import secrets
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
db = ExcelDB()

# Configure CORS for all API endpoints
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-CSRF-Token"]
    }
})

# Security Headers
@app.after_request
def add_security_headers(response):
    # Clickjacking protection - VULNERABLE: Allow events page to be framed
    if request.endpoint == 'events':
        # Make events page vulnerable to clickjacking
        response.headers['X-Frame-Options'] = 'ALLOWALL'
    else:
        # Protect all other pages
        response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # XSS Protection - DISABLED for events page to allow XSS demo
    if request.endpoint == 'events':
        # Disable XSS protection for events page (vulnerable)
        response.headers['X-XSS-Protection'] = '0'
    else:
        response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Strict Transport Security (HTTPS)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy - Allow framing for events page
    if request.endpoint == 'events':
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self';"
        )
    else:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy
    response.headers['Permissions-Policy'] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "speaker=()"
    )
    
    # Cache Control for sensitive pages
    if request.endpoint in ['login', 'admin_dashboard', 'organizer_dashboard', 'user_dashboard']:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Session Configuration - VULNERABLE: No security attributes
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Allow HTTP transmission
    SESSION_COOKIE_HTTPONLY=False,  # Allow JavaScript access
    SESSION_COOKIE_SAMESITE=None,  # No CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)  # Session timeout
)

# Global error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled Exception: {str(e)}')
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    else:
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('home'))

# Rate limiting for coupon codes
coupon_attempts = defaultdict(list)
COUPON_RATE_LIMIT = 3  # Max 3 attempts per minute
COUPON_WINDOW = 60  # 60 seconds

# Global API rate limiting
api_attempts = defaultdict(list)
API_RATE_LIMIT = 5  # Max 5 requests per minute
API_WINDOW = 60  # 1 minute

# JWT and security
JWT_SECRET = 'your-jwt-secret-key'
login_attempts = defaultdict(list)
LOGIN_RATE_LIMIT = 5  # Max 5 attempts per minute
LOGIN_WINDOW = 60  # 1 minute
password_reset_tokens = {}  # Store reset tokens

# CSRF Protection
def generate_csrf_token():
    """Generate CSRF token"""
    return secrets.token_hex(32)

def validate_csrf_token(token):
    """Validate CSRF token"""
    return token and session.get('csrf_token') == token

def csrf_required(f):
    """Decorator for CSRF protection"""
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            # Get CSRF token from header or form
            csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token') or request.json.get('csrf_token') if request.is_json else None
            
            if not validate_csrf_token(csrf_token):
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'CSRF token missing or invalid'}), 403
                else:
                    flash('Security error: Invalid request', 'error')
                    return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Valid coupon codes
VALID_COUPONS = {
    'SAVE10': 0.10,  # 10% discount
    'SAVE20': 0.20,  # 20% discount
    'EARLY50': 0.50  # 50% discount
}

def get_dynamic_price(event):
    """Calculate dynamic price based on event date proximity"""
    try:
        if not event or 'Date' not in event or 'Price' not in event:
            return 0
        
        event_date = datetime.strptime(event['Date'], '%Y-%m-%d')
        current_date = datetime.now()
        days_until_event = (event_date - current_date).days
        
        base_price = float(event['Price'])
        
        # If event is within 7 days, increase price by 50%
        if 0 <= days_until_event <= 7:
            return base_price * 1.5
        else:
            return base_price
    except (ValueError, TypeError, KeyError) as e:
        app.logger.error(f'Dynamic pricing error: {str(e)}')
        return float(event.get('Price', 0)) if event else 0

def is_rate_limited(user_id):
    """Check if user is rate limited for coupon attempts"""
    try:
        if not user_id:
            return True
        
        now = time.time()
        user_attempts = coupon_attempts.get(user_id, [])
        
        # Remove old attempts outside the window
        coupon_attempts[user_id] = [attempt for attempt in user_attempts if now - attempt < COUPON_WINDOW]
        
        return len(coupon_attempts[user_id]) >= COUPON_RATE_LIMIT
    except Exception as e:
        app.logger.error(f'Rate limiting error: {str(e)}')
        return True  # Fail safe - block if error

def add_coupon_attempt(user_id):
    """Record a coupon attempt"""
    coupon_attempts[user_id].append(time.time())

def validate_coupon(coupon_code):
    """Validate coupon code and return discount"""
    try:
        if not coupon_code or not isinstance(coupon_code, str):
            return 0
        
        # Sanitize input
        coupon_code = coupon_code.strip().upper()
        
        # Length check
        if len(coupon_code) > 20:
            return 0
        
        # Only allow alphanumeric characters
        import re
        if not re.match(r'^[A-Z0-9]+$', coupon_code):
            return 0
        
        return VALID_COUPONS.get(coupon_code, 0)
    except Exception as e:
        app.logger.error(f'Coupon validation error: {str(e)}')
        return 0

def generate_jwt_token(user_data):
    """Generate JWT token for user"""
    try:
        if not user_data or not all(k in user_data for k in ['UserID', 'Email', 'Role']):
            return None
        
        payload = {
            'user_id': user_data['UserID'],
            'email': user_data['Email'],
            'role': user_data['Role'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    except Exception as e:
        app.logger.error(f'JWT generation error: {str(e)}')
        return None

def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        if not token:
            return None
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        app.logger.info('JWT token expired')
        return None
    except jwt.InvalidTokenError:
        app.logger.warning('Invalid JWT token')
        return None
    except Exception as e:
        app.logger.error(f'JWT verification error: {str(e)}')
        return None

def is_login_rate_limited(email):
    """Check if login attempts are rate limited"""
    now = time.time()
    attempts = login_attempts[email]
    login_attempts[email] = [attempt for attempt in attempts if now - attempt < LOGIN_WINDOW]
    return len(login_attempts[email]) >= LOGIN_RATE_LIMIT

def add_login_attempt(email):
    """Record a login attempt"""
    login_attempts[email].append(time.time())

def is_api_rate_limited(client_ip):
    """Check if API requests are rate limited"""
    now = time.time()
    attempts = api_attempts[client_ip]
    api_attempts[client_ip] = [attempt for attempt in attempts if now - attempt < API_WINDOW]
    return len(api_attempts[client_ip]) >= API_RATE_LIMIT

def add_api_attempt(client_ip):
    """Record an API attempt"""
    api_attempts[client_ip].append(time.time())

def api_rate_limit_required(f):
    """Decorator for API rate limiting"""
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr or 'unknown'
        
        if is_api_rate_limited(client_ip):
            return jsonify({'success': False, 'message': 'Rate limit exceeded. Max 5 requests per minute.'}), 429
        
        add_api_attempt(client_ip)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def generate_reset_token(email):
    """Generate password reset token"""
    token = secrets.token_urlsafe(32)
    password_reset_tokens[token] = {
        'email': email,
        'expires': time.time() + 3600  # 1 hour
    }
    return token

def verify_reset_token(token):
    """Verify password reset token"""
    if token in password_reset_tokens:
        data = password_reset_tokens[token]
        if time.time() < data['expires']:
            return data['email']
        else:
            del password_reset_tokens[token]
    return None

@app.route('/')
def home():
    events = db.get_events()
    # Filter out organizer-only events for regular users
    if 'user_role' not in session or session.get('user_role') == 'user':
        events = [e for e in events if e and e.get('Category') != 'Organizer-Only']
    
    # Add dynamic pricing
    for event in events:
        event['DynamicPrice'] = get_dynamic_price(event)
        event['PriceIncreased'] = event['DynamicPrice'] > event['Price']
    
    return render_template('home.html', events=events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'GET':
            # Generate CSRF token for form
            if 'csrf_token' not in session:
                session['csrf_token'] = generate_csrf_token()
        
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email and password are required!', 'error')
                return render_template('login.html')
            
            # Rate limiting check
            if is_login_rate_limited(email):
                flash('Too many login attempts. Please try again later.', 'error')
                return render_template('login.html')
            
            user = db.authenticate_user(email, password)
            
            if user is not None:
                # Reset failed attempts on successful login
                session.pop('failed_attempts', None)
                session.permanent = True
                session['user_id'] = user['UserID']
                session['user_name'] = user['Name']
                session['user_role'] = user['Role']
                session['csrf_token'] = generate_csrf_token()  # New token after login
                
                # Default role-based redirect
                if user['Role'] == 'admin':
                    response = redirect(url_for('admin_dashboard'))
                elif user['Role'] == 'organizer':
                    response = redirect(url_for('organizer_dashboard'))
                else:
                    response = redirect(url_for('user_dashboard'))
                
                # Set vulnerable cookies with plain text credentials
                response.set_cookie('username', email, 
                                  secure=True, httponly=True, samesite='Strict', 
                                  max_age=7200)  # 2 hours
                response.set_cookie('password', password, 
                                  secure=True, httponly=True, samesite='Strict', 
                                  max_age=7200)  # 2 hours
                
                flash('Login successful!', 'success')
                return response
            else:
                # Track failed attempts and add rate limiting
                failed_attempts = session.get('failed_attempts', 0) + 1
                session['failed_attempts'] = failed_attempts
                add_login_attempt(email)
                flash(f'Invalid credentials! Failed attempts: {failed_attempts}', 'error')
        
        return render_template('login.html')
    except Exception as e:
        flash('Login system error. Please try again.', 'error')
        app.logger.error(f'Login error: {str(e)}')
        return render_template('login.html')

@app.route('/csrf-token')
def get_csrf_token():
    """API endpoint to get CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = generate_csrf_token()
    return jsonify({'csrf_token': session['csrf_token']})

@app.route('/api/login', methods=['POST'])
@csrf_required
@api_rate_limit_required
def api_login():
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400
        
        # Rate limiting check
        if is_login_rate_limited(email):
            return jsonify({'success': False, 'message': 'Too many login attempts. Please try again later.'}), 429
        
        user = db.authenticate_user(email, password)
        if user:
            # Reset failed attempts on successful login
            session.pop('failed_attempts', None)
            session['user_id'] = user['UserID']
            session['user_name'] = user['Name']
            session['user_role'] = user['Role']
            session['csrf_token'] = generate_csrf_token()  # New token after login
            
            # VULNERABLE: Store credentials in plain text cookies via API
            response = jsonify({'success': True, 'user': user, 'message': 'Login successful', 'csrf_token': session['csrf_token']})
            response.set_cookie('username', email, 
                              secure=True, httponly=True, samesite='Strict', 
                              max_age=7200)  # 2 hours
            response.set_cookie('password', password, 
                              secure=True, httponly=True, samesite='Strict', 
                              max_age=7200)  # 2 hours
            return response
        else:
            # Track failed attempts and add rate limiting
            failed_attempts = session.get('failed_attempts', 0) + 1
            session['failed_attempts'] = failed_attempts
            add_login_attempt(email)
            return jsonify({'success': False, 'message': f'Invalid credentials! Failed attempts: {failed_attempts}'}), 401
    except Exception as e:
        app.logger.error(f'API login error: {str(e)}')
        return jsonify({'success': False, 'message': 'Login system error'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():  # VULNERABLE: No CSRF protection
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')
        
        try:
            user_id = db.add_user(name, email, role, password)
            flash('Registration successful!', 'success')
            
            # VULNERABLE: Open redirect after successful registration
            redirect_url = request.args.get('redirect') or request.form.get('redirect')
            
            if redirect_url:
                # No validation - redirect to any URL!
                return redirect(redirect_url)
            else:
                # Default redirect to login
                return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed!', 'error')
    
    return render_template('register.html')

@app.route('/api/register', methods=['POST'])
@cross_origin()
@csrf_required
@api_rate_limit_required
def api_register():
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'user')
        
        if not all([name, email, password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if role not in ['user', 'organizer', 'admin']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        user_id = db.add_user(name, email, role, password)
        return jsonify({'success': True, 'user_id': user_id, 'message': 'Registration successful'})
    except Exception as e:
        app.logger.error(f'API register error: {str(e)}')
        return jsonify({'success': False, 'message': 'Registration failed'}), 400

@app.route('/logout')
def logout():
    # Secure logout - clear all session data
    session.clear()
    flash('Logged out successfully!', 'success')
    response = redirect(url_for('home'))
    # Clear any cached data
    response.headers['Clear-Site-Data'] = '"cache", "cookies", "storage"'
    # Clear vulnerable cookies
    response.set_cookie('username', '', expires=0)
    response.set_cookie('password', '', expires=0)
    return response

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    if user_id <= 3:
        flash('Cannot delete default users!', 'error')
    elif db.delete_user(user_id, session['user_id']):
        flash('User deleted successfully!', 'success')
    else:
        flash('Failed to delete user!', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_delete_event/<int:event_id>')
def admin_delete_event(event_id):
    try:
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Access denied!', 'error')
            return redirect(url_for('login'))
        
        if event_id <= 3:
            flash('Cannot delete default events!', 'error')
        elif db.admin_delete_event(event_id):
            flash('Event and all related bookings deleted successfully!', 'success')
        else:
            flash('Failed to delete event!', 'error')
        
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        app.logger.error(f'Admin delete event error: {str(e)}')
        flash('Error deleting event. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    users = db.get_users()
    events = db.get_events()
    bookings = db.get_bookings()
    
    return render_template('admin_dashboard.html', 
                         users=users,
                         events=events,
                         bookings=bookings)

@app.route('/organizer')
def organizer_dashboard():
    if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    events = db.get_events()
    user_events = [e for e in events if e and e.get('OrganizerID') == session['user_id']]
    
    # Get booking counts for each event
    bookings = db.get_bookings()
    for event in user_events:
        event_bookings = [b for b in bookings if b and b.get('EventID') == event['EventID'] and b.get('Status') == 'Confirmed']
        event['BookingCount'] = len(event_bookings)
    
    return render_template('organizer_dashboard.html', events=user_events)

@app.route('/delete_event/<int:event_id>')
def delete_event(event_id):
    if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    if event_id <= 3:
        flash('Cannot delete default events!', 'error')
    elif db.delete_event(event_id, session['user_id']):
        flash('Event deleted successfully!', 'success')
    else:
        flash('Cannot delete event with existing bookings!', 'error')
    
    return redirect(url_for('organizer_dashboard'))

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@cross_origin()
@csrf_required
@api_rate_limit_required
def api_delete_event(event_id):
    try:
        if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        if event_id <= 0:
            return jsonify({'success': False, 'message': 'Invalid event ID'}), 400
        
        if event_id <= 3:
            return jsonify({'success': False, 'message': 'Cannot delete default events'}), 400
        
        if db.delete_event(event_id, session['user_id']):
            return jsonify({'success': True, 'message': 'Event deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Cannot delete event with existing bookings'}), 400
    except Exception as e:
        app.logger.error(f'API delete event error: {str(e)}')
        return jsonify({'success': False, 'message': 'Delete operation failed'}), 500

@app.route('/cancel_event/<int:event_id>')
def cancel_event(event_id):
    if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    if event_id <= 3:
        flash('Cannot cancel default events!', 'error')
    elif db.cancel_event(event_id, session['user_id']):
        flash('Event cancelled and all bookings refunded!', 'success')
    else:
        flash('Failed to cancel event!', 'error')
    
    return redirect(url_for('organizer_dashboard'))

@app.route('/api/events/<int:event_id>/cancel', methods=['POST'])
@cross_origin()
@csrf_required
@api_rate_limit_required
def api_cancel_event(event_id):
    try:
        if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        if event_id <= 0:
            return jsonify({'success': False, 'message': 'Invalid event ID'}), 400
        
        if event_id <= 3:
            return jsonify({'success': False, 'message': 'Cannot cancel default events'}), 400
        
        if db.cancel_event(event_id, session['user_id']):
            return jsonify({'success': True, 'message': 'Event cancelled and all bookings refunded'})
        else:
            return jsonify({'success': False, 'message': 'Failed to cancel event'}), 400
    except Exception as e:
        app.logger.error(f'API cancel event error: {str(e)}')
        return jsonify({'success': False, 'message': 'Cancel operation failed'}), 500

@app.route('/user')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    user_bookings = db.get_user_bookings_with_events(session['user_id'])
    
    return render_template('user_dashboard.html', bookings=user_bookings)

@app.route('/create_event', methods=['GET', 'POST'])
@csrf_required
def create_event():
    try:
        if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
            flash('Access denied!', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            try:
                title = request.form.get('title', '').strip()
                category = request.form.get('category', '')
                visibility = request.form.get('visibility', '')
                date = request.form.get('date', '')
                venue = request.form.get('venue', '').strip()
                total_seats = int(request.form.get('total_seats', 0))
                price = float(request.form.get('price', 0))
                
                if not all([title, category, visibility, date, venue]) or total_seats <= 0 or price < 0:
                    flash('All fields are required and must be valid!', 'error')
                    return render_template('create_event.html')
                
                if visibility == 'organizer-only':
                    category = 'Organizer-Only'
                
                event_id = db.add_event(title, category, date, venue, session['user_id'], total_seats, price)
                if event_id:
                    flash('Event created successfully!', 'success')
                    return redirect(url_for('organizer_dashboard'))
                else:
                    flash('Failed to create event!', 'error')
            except ValueError:
                flash('Invalid number format for seats or price!', 'error')
            except Exception as e:
                flash('Error creating event. Please try again.', 'error')
                app.logger.error(f'Event creation error: {str(e)}')
        
        return render_template('create_event.html')
    except Exception as e:
        flash('System error. Please try again.', 'error')
        app.logger.error(f'Create event page error: {str(e)}')
        return redirect(url_for('organizer_dashboard'))

@app.route('/api/events', methods=['GET', 'POST'])
@cross_origin()
@csrf_required
@api_rate_limit_required
def api_events():
    try:
        if request.method == 'GET':
            events = db.get_events()
            return jsonify({'success': True, 'events': events})
        
        elif request.method == 'POST':
            if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
            
            data = request.get_json() or {}
            title = data.get('title', '').strip()
            category = data.get('category', '')
            visibility = data.get('visibility', '')
            date = data.get('date', '')
            venue = data.get('venue', '').strip()
            
            try:
                total_seats = int(data.get('total_seats', 0))
                price = float(data.get('price', 0))
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Invalid seats or price format'}), 400
            
            if not all([title, category, visibility, date, venue]) or total_seats <= 0 or price < 0:
                return jsonify({'success': False, 'message': 'All fields required and must be valid'}), 400
            
            if visibility == 'organizer-only':
                category = 'Organizer-Only'
            
            event_id = db.add_event(title, category, date, venue, session['user_id'], total_seats, price)
            if event_id:
                return jsonify({'success': True, 'event_id': event_id, 'message': 'Event created successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to create event'}), 500
    except Exception as e:
        app.logger.error(f'API events error: {str(e)}')
        return jsonify({'success': False, 'message': 'System error'}), 500

@app.route('/book/<int:event_id>', methods=['GET', 'POST'])
def book_event(event_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    events = db.get_events()
    event = None
    for e in events:
        if e and e.get('EventID') == event_id:
            event = e
            break
    
    if not event:
        flash('Event not found!', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        seats_booked = int(request.form['seats'])
        
        if seats_booked > event['AvailableSeats']:
            flash('Not enough seats available!', 'error')
        else:
            # Redirect to checkout instead of direct booking
            return redirect(url_for('checkout', event_id=event_id, seats=seats_booked))
    
    return render_template('book_event.html', event=event)

@app.route('/checkout/<int:event_id>/<int:seats>', methods=['GET', 'POST'])
@csrf_required
def checkout(event_id, seats):
    try:
        if 'user_id' not in session:
            flash('Please login first!', 'error')
            return redirect(url_for('login'))
        
        if seats <= 0 or seats > 100:  # Reasonable limit
            flash('Invalid number of seats!', 'error')
            return redirect(url_for('home'))
        
        events = db.get_events()
        event = None
        for e in events:
            if e and e.get('EventID') == event_id:
                event = e
                break
        
        if not event:
            flash('Event not found!', 'error')
            return redirect(url_for('home'))
        
        if seats > event.get('AvailableSeats', 0):
            flash('Not enough seats available!', 'error')
            return redirect(url_for('home'))
        
        dynamic_price = get_dynamic_price(event)
        total_price = dynamic_price * seats
        
        if request.method == 'POST':
            try:
                card_number = request.form.get('card_number', '').replace(' ', '')
                card_expiry = request.form.get('card_expiry', '')
                card_cvv = request.form.get('card_cvv', '')
                card_name = request.form.get('card_name', '').strip()
                coupon_code = request.form.get('coupon_code', '').strip()
                
                if not all([card_number, card_expiry, card_cvv, card_name]):
                    flash('All payment fields are required!', 'error')
                    return render_template('checkout.html', event=event, seats=seats, total_price=total_price, dynamic_price=dynamic_price)
                
                # Apply coupon if provided
                if coupon_code:
                    if is_rate_limited(session['user_id']):
                        flash('Too many coupon attempts. Please try again later.', 'error')
                        return render_template('checkout.html', event=event, seats=seats, total_price=total_price, dynamic_price=dynamic_price)
                    
                    add_coupon_attempt(session['user_id'])
                    discount = validate_coupon(coupon_code)
                    if discount > 0:
                        total_price = total_price * (1 - discount)
                        flash(f'Coupon applied! {discount*100}% discount', 'success')
                    else:
                        flash('Invalid coupon code!', 'error')
                
                # Validate card
                if not validate_card(card_number, card_expiry, card_cvv, card_name):
                    flash('Invalid card details!', 'error')
                    return render_template('checkout.html', event=event, seats=seats, total_price=total_price, dynamic_price=dynamic_price)
                
                # Process payment and book
                booking_id = db.book_tickets_with_payment(session['user_id'], event_id, seats, total_price, card_number[-4:])
                if booking_id:
                    flash(f'Payment successful! Booking ID: {booking_id}', 'success')
                    return redirect(url_for('user_dashboard'))
                else:
                    flash('Payment failed! Please try again.', 'error')
            except Exception as e:
                flash('Payment processing error. Please try again.', 'error')
                app.logger.error(f'Payment error: {str(e)}')
        
        return render_template('checkout.html', event=event, seats=seats, total_price=total_price, dynamic_price=dynamic_price)
    except Exception as e:
        flash('Checkout system error. Please try again.', 'error')
        app.logger.error(f'Checkout error: {str(e)}')
        return redirect(url_for('home'))

@app.route('/api/bookings', methods=['POST'])
@cross_origin()
@api_rate_limit_required
def api_book_tickets():  # VULNERABLE: No CSRF protection
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        data = request.get_json() or {}
        
        try:
            event_id = int(data.get('event_id', 0))
            seats = int(data.get('seats', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid event ID or seats'}), 400
        
        card_number = data.get('card_number', '').replace(' ', '')
        card_expiry = data.get('card_expiry', '')
        card_cvv = data.get('card_cvv', '')
        card_name = data.get('card_name', '').strip()
        coupon_code = data.get('coupon_code', '').strip()
        
        if not all([card_number, card_expiry, card_cvv, card_name]) or seats <= 0:
            return jsonify({'success': False, 'message': 'All fields required and seats must be positive'}), 400
        
        events = db.get_events()
        event = None
        for e in events:
            if e and e.get('EventID') == event_id:
                event = e
                break
        
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        
        if seats > event.get('AvailableSeats', 0):
            return jsonify({'success': False, 'message': 'Not enough seats available'}), 400
        
        dynamic_price = get_dynamic_price(event)
        total_price = dynamic_price * seats
        
        # Apply coupon if provided
        coupon_applied = False
        if coupon_code:
            if is_rate_limited(session['user_id']):
                return jsonify({'success': False, 'message': 'Too many coupon attempts. Please try again later.'}), 429
            
            add_coupon_attempt(session['user_id'])
            discount = validate_coupon(coupon_code)
            if discount > 0:
                total_price = total_price * (1 - discount)
                coupon_applied = True
        
        # Validate card
        if not validate_card(card_number, card_expiry, card_cvv, card_name):
            return jsonify({'success': False, 'message': 'Invalid card details'}), 400
        
        # Process payment and book
        booking_id = db.book_tickets_with_payment(session['user_id'], event_id, seats, total_price, card_number[-4:])
        if booking_id:
            message = 'Payment successful!'
            if coupon_applied:
                message += f' Coupon applied: {coupon_code.upper()}'
            return jsonify({'success': True, 'booking_id': booking_id, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Payment failed'}), 500
    except Exception as e:
        app.logger.error(f'API booking error: {str(e)}')
        return jsonify({'success': False, 'message': 'Booking system error'}), 500

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    if db.cancel_booking(booking_id, session['user_id']):
        flash('Booking cancelled successfully!', 'success')
    else:
        flash('Cancellation failed!', 'error')
    
    return redirect(url_for('user_dashboard'))

@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
@cross_origin()
@csrf_required
@api_rate_limit_required
def api_cancel_booking(booking_id):
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        if booking_id <= 0:
            return jsonify({'success': False, 'message': 'Invalid booking ID'}), 400
        
        if db.cancel_booking(booking_id, session['user_id']):
            return jsonify({'success': True, 'message': 'Booking cancelled successfully'})
        else:
            return jsonify({'success': False, 'message': 'Cancellation failed'}), 400
    except Exception as e:
        app.logger.error(f'API cancel booking error: {str(e)}')
        return jsonify({'success': False, 'message': 'Cancellation operation failed'}), 500

def validate_card(card_number, expiry, cvv, name):
    try:
        # Input validation
        if not all([card_number, expiry, cvv, name]):
            return False
        
        # Sanitize inputs
        card_number = str(card_number).replace(' ', '').replace('-', '')
        expiry = str(expiry).strip()
        cvv = str(cvv).strip()
        name = str(name).strip()
        
        # Card number validation (Luhn algorithm)
        if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
            return False
        
        # Luhn algorithm
        def luhn_check(card_num):
            try:
                digits = [int(d) for d in card_num]
                for i in range(len(digits) - 2, -1, -2):
                    digits[i] *= 2
                    if digits[i] > 9:
                        digits[i] -= 9
                return sum(digits) % 10 == 0
            except (ValueError, IndexError):
                return False
        
        if not luhn_check(card_number):
            return False
        
        # Expiry validation (MM/YY format)
        if len(expiry) != 5 or expiry[2] != '/' or not expiry[:2].isdigit() or not expiry[3:].isdigit():
            return False
        
        try:
            month, year = int(expiry[:2]), int(expiry[3:])
            if month < 1 or month > 12:
                return False
            
            # Check if card is not expired
            current_year = datetime.now().year % 100
            current_month = datetime.now().month
            
            if year < current_year or (year == current_year and month < current_month):
                return False
                
        except ValueError:
            return False
        
        # CVV validation
        if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
            return False
        
        # Name validation - prevent XSS and injection
        import re
        if not re.match(r'^[A-Za-z\s\.\-]{2,50}$', name):
            return False
        
        return True
    except Exception as e:
        app.logger.error(f'Card validation error: {str(e)}')
        return False

@app.route('/events')
def events():
    events = db.get_events()
    # Filter out organizer-only events for regular users
    if 'user_role' not in session or session.get('user_role') == 'user':
        events = [e for e in events if e and e.get('Category') != 'Organizer-Only']
    
    # Add dynamic pricing
    for event in events:
        event['DynamicPrice'] = get_dynamic_price(event)
    
    # Advanced filtering
    category = request.args.get('category')
    city = request.args.get('city')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    sort_by = request.args.get('sort_by', 'date')
    
    # VULNERABLE: Reflected XSS in search parameter (no sanitization)
    search_query = request.args.get('search', '')
    
    if category:
        events = [e for e in events if e and e.get('Category') == category]
    if city:
        events = [e for e in events if e and e.get('Venue') and city.lower() in e['Venue'].lower()]
    if date_from:
        events = [e for e in events if e and e.get('Date') >= date_from]
    if date_to:
        events = [e for e in events if e and e.get('Date') <= date_to]
    if price_min:
        events = [e for e in events if e and e.get('DynamicPrice', 0) >= float(price_min)]
    if price_max:
        events = [e for e in events if e and e.get('DynamicPrice', 0) <= float(price_max)]
    
    # Search functionality (vulnerable to XSS)
    if search_query:
        events = [e for e in events if e and (
            search_query.lower() in e.get('Title', '').lower() or
            search_query.lower() in e.get('Category', '').lower() or
            search_query.lower() in e.get('Venue', '').lower()
        )]
    
    # Sorting
    if sort_by == 'price_low':
        events.sort(key=lambda x: x.get('DynamicPrice', 0))
    elif sort_by == 'price_high':
        events.sort(key=lambda x: x.get('DynamicPrice', 0), reverse=True)
    elif sort_by == 'name':
        events.sort(key=lambda x: x.get('Title', ''))
    else:  # date
        events.sort(key=lambda x: x.get('Date', ''))
    
    return render_template('events.html', events=events, search_query=search_query)

@app.route('/api/bookings')
@cross_origin()
@api_rate_limit_required
def api_get_bookings():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        bookings = db.get_user_bookings_with_events(session['user_id'])
        return jsonify({'success': True, 'bookings': bookings or []})
    except Exception as e:
        app.logger.error(f'API get bookings error: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to retrieve bookings'}), 500

@app.route('/api/events/<int:event_id>/attendees')
@cross_origin()
@api_rate_limit_required
def api_event_attendees(event_id):
    try:
        if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        if event_id <= 0:
            return jsonify({'success': False, 'message': 'Invalid event ID'}), 400
        
        # Verify ownership
        events = db.get_events()
        event = None
        for e in events:
            if e and e.get('EventID') == event_id:
                if session.get('user_role') != 'admin' and e.get('OrganizerID') != session['user_id']:
                    return jsonify({'success': False, 'message': 'Access denied'}), 403
                event = e
                break
        
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        
        attendees = db.get_event_attendees(event_id)
        return jsonify({'success': True, 'event': event, 'attendees': attendees or []})
    except Exception as e:
        app.logger.error(f'API event attendees error: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to retrieve attendees'}), 500

@app.route('/event_attendees/<int:event_id>')
def event_attendees(event_id):
    if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    # Get event details and verify ownership
    events = db.get_events()
    event = None
    for e in events:
        if e and e.get('EventID') == event_id:
            if session.get('user_role') != 'admin' and e.get('OrganizerID') != session['user_id']:
                flash('Access denied!', 'error')
                return redirect(url_for('organizer_dashboard'))
            event = e
            break
    
    if not event:
        flash('Event not found!', 'error')
        return redirect(url_for('organizer_dashboard'))
    
    # Get attendees with user details
    attendees = db.get_event_attendees(event_id)
    
    return render_template('event_attendees.html', event=event, attendees=attendees)

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@csrf_required
def edit_event(event_id):
    if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    # Get event and verify ownership
    events = db.get_events()
    event = None
    for e in events:
        if e and e.get('EventID') == event_id:
            if session.get('user_role') != 'admin' and e.get('OrganizerID') != session['user_id']:
                flash('Access denied!', 'error')
                return redirect(url_for('organizer_dashboard'))
            event = e
            break
    
    if not event:
        flash('Event not found!', 'error')
        return redirect(url_for('organizer_dashboard'))
    
    if event_id <= 3:
        flash('Cannot edit default events!', 'error')
        return redirect(url_for('organizer_dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        visibility = request.form['visibility']
        date = request.form['date']
        venue = request.form['venue']
        total_seats = int(request.form['total_seats'])
        price = float(request.form['price'])
        
        if visibility == 'organizer-only':
            category = 'Organizer-Only'
        
        if db.update_event(event_id, session['user_id'], title, category, date, venue, total_seats, price):
            flash('Event updated successfully!', 'success')
            return redirect(url_for('organizer_dashboard'))
        else:
            flash('Failed to update event!', 'error')
    
    return render_template('edit_event.html', event=event)

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@cross_origin()
@csrf_required
@api_rate_limit_required
def api_update_event(event_id):
    try:
        if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        if event_id <= 0:
            return jsonify({'success': False, 'message': 'Invalid event ID'}), 400
        
        if event_id <= 3:
            return jsonify({'success': False, 'message': 'Cannot edit default events'}), 400
        
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        category = data.get('category', '')
        visibility = data.get('visibility', '')
        date = data.get('date', '')
        venue = data.get('venue', '').strip()
        
        try:
            total_seats = int(data.get('total_seats', 0))
            price = float(data.get('price', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid seats or price format'}), 400
        
        if not all([title, category, visibility, date, venue]) or total_seats <= 0 or price < 0:
            return jsonify({'success': False, 'message': 'All fields required and must be valid'}), 400
        
        if visibility == 'organizer-only':
            category = 'Organizer-Only'
        
        if db.update_event(event_id, session['user_id'], title, category, date, venue, total_seats, price):
            return jsonify({'success': True, 'message': 'Event updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update event'}), 400
    except Exception as e:
        app.logger.error(f'API update event error: {str(e)}')
        return jsonify({'success': False, 'message': 'Update operation failed'}), 500

@app.route('/api/soap/validate_coupon', methods=['POST'])
@cross_origin()
@api_rate_limit_required
def soap_validate_coupon():  # VULNERABLE: No CSRF protection
    """SOAP-style API for coupon validation with rate limiting"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'soap:Envelope': {
                    'soap:Body': {
                        'ValidateCouponResponse': {
                            'success': False,
                            'message': 'Authentication required'
                        }
                    }
                }
            }), 401
        
        data = request.get_json() or {}
        coupon_code = data.get('coupon_code', '').strip()
        
        if not coupon_code:
            return jsonify({
                'soap:Envelope': {
                    'soap:Body': {
                        'ValidateCouponResponse': {
                            'success': False,
                            'message': 'Coupon code required',
                            'discount': 0
                        }
                    }
                }
            }), 400
        
        # Rate limiting check
        if is_rate_limited(session['user_id']):
            return jsonify({
                'soap:Envelope': {
                    'soap:Body': {
                        'ValidateCouponResponse': {
                            'success': False,
                            'message': 'Rate limit exceeded. Max 3 attempts per minute.',
                            'discount': 0,
                            'rate_limited': True
                        }
                    }
                }
            }), 429
        
        # Record attempt
        add_coupon_attempt(session['user_id'])
        
        # Validate coupon
        discount = validate_coupon(coupon_code)
        
        if discount > 0:
            return jsonify({
                'soap:Envelope': {
                    'soap:Body': {
                        'ValidateCouponResponse': {
                            'success': True,
                            'message': f'Valid coupon: {discount*100}% discount',
                            'discount': discount,
                            'coupon_code': coupon_code.upper()
                        }
                    }
                }
            })
        else:
            return jsonify({
                'soap:Envelope': {
                    'soap:Body': {
                        'ValidateCouponResponse': {
                            'success': False,
                            'message': 'Invalid coupon code',
                            'discount': 0
                        }
                    }
                }
            }), 400
    except Exception as e:
        app.logger.error(f'SOAP validate coupon error: {str(e)}')
        return jsonify({
            'soap:Envelope': {
                'soap:Body': {
                    'ValidateCouponResponse': {
                        'success': False,
                        'message': 'Coupon validation system error',
                        'discount': 0
                    }
                }
            }
        }), 500

@app.route('/api/dynamic_price/<int:event_id>')
@cross_origin()
@api_rate_limit_required
def api_dynamic_price(event_id):
    """Get dynamic price for an event"""
    try:
        if event_id <= 0:
            return jsonify({'success': False, 'message': 'Invalid event ID'}), 400
        
        events = db.get_events()
        event = None
        for e in events:
            if e and e.get('EventID') == event_id:
                event = e
                break
        
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        
        dynamic_price = get_dynamic_price(event)
        base_price = float(event.get('Price', 0))
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'base_price': base_price,
            'dynamic_price': dynamic_price,
            'price_increased': dynamic_price > base_price,
            'increase_percentage': ((dynamic_price - base_price) / base_price * 100) if dynamic_price > base_price else 0
        })
    except Exception as e:
        app.logger.error(f'API dynamic price error: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to calculate dynamic price'}), 500

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        users = db.get_users()
        user_exists = any(u and u.get('Email') == email for u in users)
        
        if user_exists:
            token = generate_reset_token(email)
            flash(f'Reset link: /reset_password/{token}', 'success')
        else:
            flash('If email exists, reset link has been sent.', 'success')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset token!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form['password']
        if db.update_password(email, new_password):
            del password_reset_tokens[token]
            flash('Password updated successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Failed to update password!', 'error')
    
    return render_template('reset_password.html', token=token)

@app.route('/api/jwt_login', methods=['POST'])
@cross_origin()
@api_rate_limit_required
def jwt_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Rate limiting check
    if is_login_rate_limited(email):
        return jsonify({'success': False, 'message': 'Too many login attempts. Please try again later.'}), 429
    
    user = db.authenticate_user(email, password)
    if user:
        # Reset failed attempts on successful login
        session.pop('failed_attempts', None)
        token = generate_jwt_token(user)
        return jsonify({'success': True, 'token': token, 'user': user})
    else:
        # Track failed attempts and add rate limiting
        failed_attempts = session.get('failed_attempts', 0) + 1
        session['failed_attempts'] = failed_attempts
        add_login_attempt(email)
        return jsonify({'success': False, 'message': f'Invalid credentials! Failed attempts: {failed_attempts}'}), 401

@app.route('/api/export_reports')
@cross_origin()
@api_rate_limit_required
def export_reports():
    try:
        if 'user_id' not in session or session.get('user_role') not in ['organizer', 'admin']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        events = db.get_events() or []
        bookings = db.get_bookings() or []
        
        if session.get('user_role') == 'organizer':
            events = [e for e in events if e and e.get('OrganizerID') == session['user_id']]
            event_ids = [e.get('EventID') for e in events if e]
            bookings = [b for b in bookings if b and b.get('EventID') in event_ids]
        
        total_revenue = 0
        try:
            total_revenue = sum(float(b.get('Amount', 0)) for b in bookings if b and b.get('Status') == 'Confirmed')
        except (ValueError, TypeError):
            total_revenue = 0
        
        return jsonify({
            'success': True,
            'report': {
                'events': events,
                'bookings': bookings,
                'generated_at': datetime.now().isoformat(),
                'total_revenue': total_revenue,
                'event_count': len(events),
                'booking_count': len(bookings)
            }
        })
    except Exception as e:
        app.logger.error(f'API export reports error: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to generate reports'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5005)