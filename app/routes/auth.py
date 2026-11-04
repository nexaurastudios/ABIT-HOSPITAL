from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.auth import Admin
from app.services.activity_logger import log_activity

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        admin = Admin.query.filter_by(email=email).first()

        if not admin or not admin.check_password(password):
            flash('Invalid email or password. Please verify your credentials and try again.', 'danger')
            return render_template('auth/login.html', email=email)

        if not admin.is_active:
            flash('This administrator account has been deactivated. Please contact the Super Admin.', 'warning')
            return render_template('auth/login.html', email=email)

        admin.last_login = datetime.utcnow()
        db.session.commit()

        login_user(admin, remember=remember)
        log_activity("LOGIN", "Auth", f"Administrator logged in: {admin.email}")
        flash(f"Welcome back, {admin.full_name}!", "success")

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        
        # If Data Analyst logs in, redirect directly to the Data Analyst Panel
        if admin.has_role('Data Analyst'):
            return redirect(url_for('analytics.index'))

        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity("LOGOUT", "Auth", f"Administrator logged out: {current_user.email}")
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        current_pw = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')

        if not full_name:
            flash('Full name cannot be empty.', 'danger')
            return redirect(url_for('auth.profile'))

        current_user.full_name = full_name
        current_user.phone = phone

        # Handle password change if requested
        if new_pw:
            if not current_user.check_password(current_pw):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('auth.profile'))
            if new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('auth.profile'))
            if len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'danger')
                return redirect(url_for('auth.profile'))

            current_user.set_password(new_pw)
            flash('Profile and password updated successfully.', 'success')
            log_activity("PASSWORD_CHANGE", "Auth", "Changed own account password")
        else:
            flash('Profile updated successfully.', 'success')
            log_activity("PROFILE_UPDATE", "Auth", "Updated profile details")

        db.session.commit()
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')
