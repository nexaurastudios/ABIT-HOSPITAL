from datetime import datetime, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sqlalchemy import or_, func
from app.extensions import db
from app.models.doctor import Doctor, DoctorSchedule
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.services.activity_logger import log_activity

doctors_bp = Blueprint('doctors', __name__, url_prefix='/doctors')

def generate_next_doctor_id():
    last_doc = Doctor.query.order_by(Doctor.id.desc()).first()
    if last_doc:
        try:
            seq = int(last_doc.doctor_id.split('-')[-1]) + 1
        except ValueError:
            seq = Doctor.query.count() + 1001
    else:
        seq = 1001
    return f"DOC-{seq}"

@doctors_bp.route('/')
@login_required
def list_doctors():
    search = request.args.get('search', '').strip()
    dept_id = request.args.get('department_id', type=int)
    status_filter = request.args.get('status', '').strip()

    query = Doctor.query

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Doctor.name.ilike(search_fmt),
                Doctor.doctor_id.ilike(search_fmt),
                Doctor.specialization.ilike(search_fmt)
            )
        )

    if dept_id:
        query = query.filter(Doctor.department_id == dept_id)

    if status_filter:
        query = query.filter(Doctor.availability_status == status_filter)

    doctors = query.order_by(Doctor.id.asc()).all()
    departments = Department.query.filter_by(is_active=True).all()

    # Dynamic metrics
    total_docs = Doctor.query.count()
    avail_docs = Doctor.query.filter_by(availability_status='Available').count()
    busy_docs = Doctor.query.filter_by(availability_status='Busy').count()
    leave_docs = Doctor.query.filter_by(availability_status='On Leave').count()

    return render_template(
        'doctors/list.html',
        doctors=doctors,
        departments=departments,
        search=search,
        dept_id=dept_id,
        status_filter=status_filter,
        metrics={
            'total': total_docs,
            'available': avail_docs,
            'busy': busy_docs,
            'on_leave': leave_docs
        }
    )

@doctors_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_doctor():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        qualification = request.form.get('qualification', '').strip()
        specialization = request.form.get('specialization', '').strip()
        dept_id = request.form.get('department_id', type=int)
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()
        experience = request.form.get('experience_years', default=1, type=int)
        start_time_str = request.form.get('duty_start_time', '08:00')
        end_time_str = request.form.get('duty_end_time', '16:00')
        max_cap = request.form.get('max_patient_capacity', default=25, type=int)

        if not name or not qualification or not specialization or not dept_id or not phone or not email:
            flash('Please complete all required fields for doctor registration.', 'danger')
            return redirect(url_for('doctors.create_doctor'))

        if Doctor.query.filter_by(email=email).first():
            flash('A doctor with this email address already exists.', 'danger')
            return redirect(url_for('doctors.create_doctor'))

        try:
            start_t = datetime.strptime(start_time_str, '%H:%M').time()
            end_t = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            start_t = time(8, 0)
            end_t = time(16, 0)

        new_doc_id = generate_next_doctor_id()
        doc = Doctor(
            doctor_id=new_doc_id,
            name=name,
            qualification=qualification,
            specialization=specialization,
            department_id=dept_id,
            phone=phone,
            email=email,
            experience_years=experience,
            duty_start_time=start_t,
            duty_end_time=end_t,
            availability_status='Available',
            max_patient_capacity=max_cap,
            is_active=True,
            is_demo=False
        )

        db.session.add(doc)
        db.session.commit()

        # Add default standard Monday-Friday schedule
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            sched = DoctorSchedule(
                doctor_id=doc.id,
                day_of_week=day,
                start_time=start_t,
                end_time=end_t,
                slot_duration_minutes=20,
                max_slots=max_cap,
                is_active=True
            )
            db.session.add(sched)
        db.session.commit()

        log_activity("CREATE_DOCTOR", "Doctors", f"Registered doctor {new_doc_id}: Dr. {name}", record_id=new_doc_id)
        flash(f"Doctor Dr. {name} ({new_doc_id}) registered successfully!", "success")
        return redirect(url_for('doctors.view_doctor', id=doc.id))

    departments = Department.query.filter_by(is_active=True).all()
    suggested_id = generate_next_doctor_id()
    return render_template('doctors/form.html', departments=departments, doctor=None, suggested_id=suggested_id)

@doctors_bp.route('/<int:id>')
@login_required
def view_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    today = datetime.utcnow().date()

    todays_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == today
    ).all()

    total_patients_handled = db.session.query(func.count(Visit.id)).filter(
        Visit.doctor_id == doctor.id,
        Visit.status == 'Completed'
    ).scalar() or 0

    avg_consult_duration = db.session.query(func.avg(Visit.consultation_duration_minutes)).filter(
        Visit.doctor_id == doctor.id,
        Visit.consultation_duration_minutes.isnot(None)
    ).scalar()
    avg_consult = round(float(avg_consult_duration), 1) if avg_consult_duration else 15.0

    schedules = DoctorSchedule.query.filter_by(doctor_id=doctor.id, is_active=True).all()

    return render_template(
        'doctors/view.html',
        doctor=doctor,
        todays_appointments=todays_appointments,
        total_patients_handled=total_patients_handled,
        avg_consult=avg_consult,
        schedules=schedules
    )

@doctors_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_doctor(id):
    doctor = Doctor.query.get_or_404(id)

    if request.method == 'POST':
        doctor.name = request.form.get('name', '').strip()
        doctor.qualification = request.form.get('qualification', '').strip()
        doctor.specialization = request.form.get('specialization', '').strip()
        doctor.department_id = request.form.get('department_id', type=int)
        doctor.phone = request.form.get('phone', '').strip()
        doctor.email = request.form.get('email', '').strip().lower()
        doctor.experience_years = request.form.get('experience_years', default=doctor.experience_years, type=int)
        doctor.max_patient_capacity = request.form.get('max_patient_capacity', default=doctor.max_patient_capacity, type=int)
        doctor.availability_status = request.form.get('availability_status', doctor.availability_status)
        
        start_time_str = request.form.get('duty_start_time')
        end_time_str = request.form.get('duty_end_time')
        if start_time_str:
            doctor.duty_start_time = datetime.strptime(start_time_str, '%H:%M').time()
        if end_time_str:
            doctor.duty_end_time = datetime.strptime(end_time_str, '%H:%M').time()

        db.session.commit()
        log_activity("EDIT_DOCTOR", "Doctors", f"Updated details for doctor {doctor.doctor_id}: Dr. {doctor.name}", record_id=doctor.doctor_id)
        flash(f"Doctor Dr. {doctor.name} updated successfully.", "success")
        return redirect(url_for('doctors.view_doctor', id=doctor.id))

    departments = Department.query.filter_by(is_active=True).all()
    return render_template('doctors/form.html', departments=departments, doctor=doctor, suggested_id=doctor.doctor_id)

@doctors_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(id):
    doctor = Doctor.query.get_or_404(id)
    new_status = request.form.get('availability_status', 'Available')

    if new_status in ['Available', 'Busy', 'On Leave', 'Not Available']:
        doctor.availability_status = new_status
        db.session.commit()
        log_activity("DOCTOR_AVAILABILITY", "Doctors", f"Changed Dr. {doctor.name} availability to {new_status}", record_id=doctor.doctor_id)
        flash(f"Dr. {doctor.name} status updated to '{new_status}'.", "info")

    return redirect(request.referrer or url_for('doctors.view_doctor', id=doctor.id))

@doctors_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    doc_name = doctor.name
    doc_id = doctor.doctor_id

    # Check for active appointments
    has_active_appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status.in_(['Scheduled', 'Confirmed', 'Waiting', 'In Consultation'])
    ).first()

    if has_active_appts:
        flash(f"Cannot delete Dr. {doc_name} because active appointments are assigned. You can set availability to 'Not Available' instead.", "danger")
        return redirect(url_for('doctors.view_doctor', id=id))

    db.session.delete(doctor)
    db.session.commit()
    log_activity("DELETE_DOCTOR", "Doctors", f"Deleted record for doctor {doc_id}: Dr. {doc_name}", record_id=doc_id)
    flash(f"Doctor Dr. {doc_name} ({doc_id}) removed.", "info")
    return redirect(url_for('doctors.list_doctors'))
