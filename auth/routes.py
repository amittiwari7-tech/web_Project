from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from core.sheets_service import post_to_sheets,authUser

# Define the auth blueprint
auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        result = authUser(email, password)  # Call the authUser function to validate credentials
        
        # TODO: Add your actual database or Google Sheets validation check here
        if result == "success":  # Assuming authUser returns "success" for valid credentials
            session['status'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('services.list_services'))
        else:
            flash('Please enter valid credentials.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        gst = request.form.get('gst')
        password = request.form.get('password')
        
        post_to_sheets('newRegister', {
            'username': username,
            'email': email,
            'phone': phone,
            'gst': gst,
            'password': password,
            'action': 'newRegister'
        })
        # TODO: Save user details, phone, and GST to your database / Google Sheets
        flash('Registration successful! Please log in with your credentials.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    # Clear the session completely or pop status
    session.clear() # Clears all session keys, forcing a clean logout state
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))