from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import func
from app.extensions import db
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.models.bed import Bed
from app.services.activity_logger import log_activity

departments_bp = Blueprint('departments', __name__, url_prefix='/departments')

@departments_bp.route('/')
@login_required
def list_departments():
    departments = Department.query.order_by(Department.name.asc()).all()
    today = date.today()

    dept_stats = []
    for dept in departments:
        total_docs = len(dept.doctors)
        avail_docs = sum(1 for d in dept.doctors if d.availability_status == 'Available' and d.is_active)
        total_patients = len(dept.patients)
        total_beds = len(dept.beds)
        occupied_beds = sum(1 for b in dept.beds if b.occupancy_status == 'Occupied')
        
        today_appts = Appointment.query.filter(
            Appointment.department_id == dept.id,
            Appointment.appointment_date == today
        ).count()

        avg_wait_val = db.session.query(func.avg(Visit.waiting_time_minutes)).filter(
            Visit.department_id == dept.id,
            Visit.waiting_time_minutes.isnot(None),
            Visit.waiting_time_minutes > 0
        ).scalar()
        avg_wait = round(float(avg_wait_val), 1) if avg_wait_val else 0.0

        # Workload calculation: today_appts + occupied_beds relative to available staff
        workload_score = (today_appts + occupied_beds) / max(1, avail_docs)

        dept_stats.append({
            'dept': dept,
            'total_docs': total_docs,
            'avail_docs': avail_docs,
            'total_patients': total_patients,
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'today_appts': today_appts,
            'avg_wait': avg_wait,
            'workload_score': round(workload_score, 1)
        })

    return render_template('departments/list.html', dept_stats=dept_stats)

@departments_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_department():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        description = request.form.get('description', '').strip()
        head = request.form.get('head_of_department', '').strip()
        floor = request.form.get('floor', '').strip()
        phone = request.form.get('phone', '').strip()

        if not name or not code:
            flash('Department Name and Code are mandatory.', 'danger')
            return redirect(url_for('departments.create_department'))

        if Department.query.filter((Department.name == name) | (Department.code == code)).first():
            flash('A department with this name or code already exists.', 'danger')
            return redirect(url_for('departments.create_department'))

        dept = Department(
            name=name,
            code=code,
            description=description,
            head_of_department=head,
            floor=floor,
            phone=phone,
            is_active=True
        )
        db.session.add(dept)
        db.session.commit()

        log_activity("CREATE_DEPARTMENT", "Departments", f"Created department {code}: {name}", record_id=str(dept.id))
        flash(f"Department '{name}' created successfully.", "success")
        return redirect(url_for('departments.view_department', id=dept.id))

    return render_template('departments/form.html', department=None)

@departments_bp.route('/<int:id>')
@login_required
def view_department(id):
    dept = Department.query.get_or_404(id)
    today = date.today()

    doctors = Doctor.query.filter_by(department_id=dept.id, is_active=True).all()
    today_appts = Appointment.query.filter(
        Appointment.department_id == dept.id,
        Appointment.appointment_date == today
    ).order_by(Appointment.appointment_time.asc()).all()

    beds = Bed.query.filter_by(department_id=dept.id).all()
    occupied_beds = sum(1 for b in beds if b.occupancy_status == 'Occupied')
    total_beds = len(beds)
    bed_pct = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

    avg_wait = db.session.query(func.avg(Visit.waiting_time_minutes)).filter(
        Visit.department_id == dept.id,
        Visit.waiting_time_minutes.isnot(None),
        Visit.waiting_time_minutes > 0
    ).scalar()

    return render_template(
        'departments/view.html',
        dept=dept,
        doctors=doctors,
        today_appts=today_appts,
        beds=beds,
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        bed_pct=bed_pct,
        avg_wait=round(float(avg_wait), 1) if avg_wait else 0.0
    )

@departments_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    dept = Department.query.get_or_404(id)

    if request.method == 'POST':
        dept.name = request.form.get('name', dept.name).strip()
        dept.description = request.form.get('description', '').strip()
        dept.head_of_department = request.form.get('head_of_department', '').strip()
        dept.floor = request.form.get('floor', '').strip()
        dept.phone = request.form.get('phone', '').strip()
        dept.is_active = bool(request.form.get('is_active'))

        db.session.commit()
        log_activity("EDIT_DEPARTMENT", "Departments", f"Updated department details for {dept.name}", record_id=str(dept.id))
        flash(f"Department '{dept.name}' updated successfully.", "success")
        return redirect(url_for('departments.view_department', id=dept.id))

    return render_template('departments/form.html', department=dept)

@departments_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_department(id):
    dept = Department.query.get_or_404(id)

    # Check for dependent doctors or beds
    if len(dept.doctors) > 0 or len(dept.beds) > 0 or len(dept.patients) > 0:
        flash(f"Cannot delete department '{dept.name}' because it contains active doctors ({len(dept.doctors)}), beds ({len(dept.beds)}), or assigned patients. Reassign or archive them first.", "danger")
        return redirect(url_for('departments.view_department', id=dept.id))

    dept_name = dept.name
    db.session.delete(dept)
    db.session.commit()
    log_activity("DELETE_DEPARTMENT", "Departments", f"Deleted department: {dept_name}")
    flash(f"Department '{dept_name}' removed.", "info")
    return redirect(url_for('departments.list_departments'))
