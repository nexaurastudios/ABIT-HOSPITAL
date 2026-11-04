import os
import sys
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.settings import HospitalSetting
from app.models.auth import Admin, Role
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.models.bed import Bed, Admission
from app.models.ml import ModelRegistry
from app.services.activity_logger import log_activity
from app.services.backup_service import generate_database_backup, clear_demo_data
from app.services.data_generator import generate_full_synthetic_dataset
from app.services.auth_decorators import role_required

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin')
def index():
    setting = HospitalSetting.get_settings()

    if request.method == 'POST':
        setting.hospital_name = request.form.get('hospital_name', setting.hospital_name).strip()
        setting.phone = request.form.get('phone', setting.phone).strip()
        setting.email = request.form.get('email', setting.email).strip()
        setting.address = request.form.get('address', setting.address).strip()
        setting.bed_capacity_alert_threshold = request.form.get('bed_capacity_alert_threshold', default=85, type=int)
        setting.waiting_time_alert_threshold = request.form.get('waiting_time_alert_threshold', default=45, type=int)
        setting.consultation_fee = request.form.get('consultation_fee', default=75.0, type=float)
        setting.system_mode = request.form.get('system_mode', setting.system_mode)

        db.session.commit()
        log_activity("UPDATE_SETTINGS", "Settings", "Updated hospital operational configurations")
        flash('Hospital settings saved successfully.', 'success')
        return redirect(url_for('settings.index'))

    return render_template('settings/index.html', setting=setting)

@settings_bp.route('/admins')
@login_required
@role_required('Super Admin')
def list_admins():
    admins = Admin.query.order_by(Admin.id.asc()).all()
    roles = Role.query.all()
    return render_template('settings/admin_list.html', admins=admins, roles=roles)

@settings_bp.route('/admins/new', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin')
def create_admin():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        role_id = request.form.get('role_id', type=int)

        if not full_name or not email or not password or not role_id:
            flash('Full Name, Email, Password, and Role are mandatory.', 'danger')
            return redirect(url_for('settings.create_admin'))

        if Admin.query.filter_by(email=email).first():
            flash('An administrator with this email already exists.', 'danger')
            return redirect(url_for('settings.create_admin'))

        role = Role.query.get(role_id)
        if not role:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('settings.create_admin'))

        admin = Admin(
            full_name=full_name,
            email=email,
            phone=phone,
            is_active=True
        )
        admin.set_password(password)
        admin.roles.append(role)

        db.session.add(admin)
        db.session.commit()

        log_activity("CREATE_ADMIN", "Settings", f"Created admin account: {email} ({role.name})", record_id=str(admin.id))
        flash(f"Administrator account for {full_name} created successfully.", "success")
        return redirect(url_for('settings.list_admins'))

    roles = Role.query.all()
    return render_template('settings/admin_form.html', admin=None, roles=roles)

@settings_bp.route('/admins/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin')
def edit_admin(id):
    admin = Admin.query.get_or_404(id)

    if request.method == 'POST':
        admin.full_name = request.form.get('full_name', admin.full_name).strip()
        admin.phone = request.form.get('phone', '').strip()
        admin.is_active = bool(request.form.get('is_active'))
        role_id = request.form.get('role_id', type=int)

        new_password = request.form.get('new_password', '')
        if new_password:
            admin.set_password(new_password)

        if role_id:
            role = Role.query.get(role_id)
            if role:
                admin.roles = [role]

        db.session.commit()
        log_activity("EDIT_ADMIN", "Settings", f"Updated admin user {admin.email}", record_id=str(admin.id))
        flash(f"Admin account for {admin.full_name} updated successfully.", "success")
        return redirect(url_for('settings.list_admins'))

    roles = Role.query.all()
    return render_template('settings/admin_form.html', admin=admin, roles=roles)

@settings_bp.route('/admins/<int:id>/toggle-active', methods=['POST'])
@login_required
@role_required('Super Admin')
def toggle_admin_active(id):
    admin = Admin.query.get_or_404(id)
    if admin.id == current_user.id:
        flash('You cannot deactivate your own administrative account.', 'warning')
        return redirect(url_for('settings.list_admins'))

    admin.is_active = not admin.is_active
    db.session.commit()
    state = "activated" if admin.is_active else "deactivated"
    log_activity("TOGGLE_ADMIN_STATUS", "Settings", f"Account {admin.email} {state}")
    flash(f"Admin account {admin.email} has been {state}.", "info")
    return redirect(url_for('settings.list_admins'))

@settings_bp.route('/backup')
@login_required
@role_required('Super Admin')
def download_backup():
    try:
        filepath, filename = generate_database_backup()
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f"Backup generation failed: {str(e)}", 'danger')
        return redirect(url_for('settings.index'))

@settings_bp.route('/clear-demo-data', methods=['POST'])
@login_required
@role_required('Super Admin')
def clear_demo():
    pw = request.form.get('confirmation_password', '')
    if not current_user.check_password(pw):
        flash('Incorrect administrator password. Demo data was not cleared.', 'danger')
        return redirect(url_for('settings.index'))

    success, msg = clear_demo_data()
    if success:
        flash(msg, 'success')
    else:
        flash(f"Error clearing demo data: {msg}", 'danger')
    return redirect(url_for('settings.index'))

@settings_bp.route('/reset-environment', methods=['POST'])
@login_required
@role_required('Super Admin')
def reset_environment():
    pw = request.form.get('confirmation_password', '')
    if not current_user.check_password(pw):
        flash('Incorrect administrator password. Environment reset aborted.', 'danger')
        return redirect(url_for('settings.index'))

    # Step 1: Clear existing demo data
    clear_demo_data()
    # Step 2: Regenerate fresh synthetic demonstration dataset
    generate_full_synthetic_dataset()

    log_activity("RESET_ENVIRONMENT", "Settings", "Reset and reseeded entire demonstration environment")
    flash('Demonstration environment reset and re-seeded successfully with fresh data.', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/system-status')
@login_required
def system_status():
    # Database connection test
    db_status = "Connected"
    db_version = "MySQL 9.x"
    try:
        ver = db.session.execute(db.text("SELECT VERSION()")).scalar()
        db_version = f"MySQL {ver}"
    except Exception as e:
        db_status = f"Error: {str(e)}"

    table_counts = {
        'Patients': Patient.query.count(),
        'Doctors': Doctor.query.count(),
        'Departments': Department.query.count(),
        'Appointments': Appointment.query.count(),
        'Visits': Visit.query.count(),
        'Beds': Bed.query.count(),
        'Admissions': Admission.query.count(),
        'Administrators': Admin.query.count(),
        'Trained ML Models': ModelRegistry.query.count()
    }

    # Disk usage
    total, used, free = shutil.disk_usage("/")
    disk_info = {
        'total_gb': round(total / (2**30), 1),
        'used_gb': round(used / (2**30), 1),
        'free_gb': round(free / (2**30), 1),
        'used_pct': round((used / total) * 100, 1)
    }

    env_info = {
        'python_version': sys.version.split()[0],
        'platform': sys.platform,
        'app_mode': HospitalSetting.get_settings().system_mode,
        'current_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    }

    return render_template(
        'settings/system_status.html',
        db_status=db_status,
        db_version=db_version,
        table_counts=table_counts,
        disk_info=disk_info,
        env_info=env_info
    )
