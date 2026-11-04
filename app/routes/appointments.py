from datetime import datetime, date, time, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sqlalchemy import or_
from app.extensions import db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.visit import Visit
from app.services.activity_logger import log_activity
from app.services.notification_service import create_notification

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

def generate_next_appointment_id():
    year_month = datetime.utcnow().strftime('%Y%m')
    prefix = f"APT-{year_month}-"
    last_appt = Appointment.query.filter(Appointment.appointment_id.like(f"{prefix}%")).order_by(Appointment.id.desc()).first()
    if last_appt:
        try:
            seq = int(last_appt.appointment_id.split('-')[-1]) + 1
        except ValueError:
            seq = Appointment.query.count() + 1
    else:
        seq = Appointment.query.count() + 1
    return f"{prefix}{seq:04d}"

@appointments_bp.route('/')
@login_required
def list_appointments():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    dept_filter = request.args.get('department_id', type=int)
    doc_filter = request.args.get('doctor_id', type=int)
    date_filter = request.args.get('date', '').strip()

    query = Appointment.query

    if search:
        search_fmt = f"%{search}%"
        query = query.join(Patient).filter(
            or_(
                Appointment.appointment_id.ilike(search_fmt),
                Patient.full_name.ilike(search_fmt),
                Patient.patient_id.ilike(search_fmt)
            )
        )

    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    if dept_filter:
        query = query.filter(Appointment.department_id == dept_filter)

    if doc_filter:
        query = query.filter(Appointment.doctor_id == doc_filter)

    if date_filter:
        try:
            filter_dt = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Appointment.appointment_date == filter_dt)
        except ValueError:
            pass

    pagination = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    departments = Department.query.filter_by(is_active=True).all()
    doctors = Doctor.query.filter_by(is_active=True).all()

    return render_template(
        'appointments/list.html',
        pagination=pagination,
        appointments=pagination.items,
        search=search,
        status_filter=status_filter,
        dept_filter=dept_filter,
        doc_filter=doc_filter,
        date_filter=date_filter,
        departments=departments,
        doctors=doctors
    )

@appointments_bp.route('/calendar')
@login_required
def calendar_view():
    departments = Department.query.filter_by(is_active=True).all()
    doctors = Doctor.query.filter_by(is_active=True).all()
    return render_template('appointments/calendar.html', departments=departments, doctors=doctors)

@appointments_bp.route('/api/calendar-events')
@login_required
def calendar_events():
    """Return appointment events formatted for FullCalendar / visual schedule"""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    dept_id = request.args.get('department_id', type=int)
    doc_id = request.args.get('doctor_id', type=int)

    query = Appointment.query

    if start_str and end_str:
        try:
            start_d = datetime.fromisoformat(start_str[:10]).date()
            end_d = datetime.fromisoformat(end_str[:10]).date()
            query = query.filter(Appointment.appointment_date.between(start_d, end_d))
        except Exception:
            pass

    if dept_id:
        query = query.filter(Appointment.department_id == dept_id)
    if doc_id:
        query = query.filter(Appointment.doctor_id == doc_id)

    appts = query.all()
    events = []
    
    color_map = {
        'Scheduled': '#3b82f6',
        'Confirmed': '#0d9488',
        'Waiting': '#f59e0b',
        'In Consultation': '#8b5cf6',
        'Completed': '#10b981',
        'Cancelled': '#ef4444',
        'No Show': '#64748b'
    }

    for a in appts:
        dt_start = datetime.combine(a.appointment_date, a.appointment_time)
        dt_end = dt_start + timedelta(minutes=20)
        events.append({
            'id': a.id,
            'title': f"{a.patient.full_name} (Dr. {a.doctor.name})",
            'start': dt_start.isoformat(),
            'end': dt_end.isoformat(),
            'backgroundColor': color_map.get(a.status, '#3b82f6'),
            'borderColor': color_map.get(a.status, '#3b82f6'),
            'extendedProps': {
                'appointment_id': a.appointment_id,
                'status': a.status,
                'department': a.department.name,
                'reason': a.reason or 'Consultation'
            }
        })

    return jsonify(events)

@appointments_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_appointment():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id', type=int)
        doctor_id = request.form.get('doctor_id', type=int)
        dept_id = request.form.get('department_id', type=int)
        appt_date_str = request.form.get('appointment_date')
        appt_time_str = request.form.get('appointment_time')
        reason = request.form.get('reason', '').strip()
        notes = request.form.get('notes', '').strip()

        # Validation 1: Required inputs
        if not patient_id or not doctor_id or not dept_id or not appt_date_str or not appt_time_str:
            flash('All appointment fields (Patient, Doctor, Department, Date, Time) are required.', 'danger')
            return redirect(url_for('appointments.create_appointment'))

        try:
            appt_date = datetime.strptime(appt_date_str, '%Y-%m-%d').date()
            appt_time = datetime.strptime(appt_time_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format provided.', 'danger')
            return redirect(url_for('appointments.create_appointment'))

        # Validation 2: Cannot schedule in the past
        if appt_date < date.today():
            flash('Cannot schedule an appointment for a past date.', 'danger')
            return redirect(url_for('appointments.create_appointment'))

        doctor = Doctor.query.get(doctor_id)
        patient = Patient.query.get(patient_id)

        if not doctor or not patient:
            flash('Specified doctor or patient record could not be found.', 'danger')
            return redirect(url_for('appointments.create_appointment'))

        # Validation 3: Doctor availability status
        if doctor.availability_status in ['On Leave', 'Not Available']:
            flash(f"Doctor Dr. {doctor.name} is currently marked as '{doctor.availability_status}'. Please select an available doctor.", 'danger')
            return redirect(url_for('appointments.create_appointment'))

        # Validation 4: Doctor duty hours
        if not (doctor.duty_start_time <= appt_time <= doctor.duty_end_time):
            flash(f"Appointment time {appt_time.strftime('%H:%M')} is outside Dr. {doctor.name}'s duty hours ({doctor.duty_start_time.strftime('%H:%M')} - {doctor.duty_end_time.strftime('%H:%M')}).", 'danger')
            return redirect(url_for('appointments.create_appointment'))

        # Validation 5: Double booking conflict check
        existing_conflict = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == appt_date,
            Appointment.appointment_time == appt_time,
            Appointment.status.notin_(['Cancelled', 'No Show'])
        ).first()

        if existing_conflict:
            flash(f"Dr. {doctor.name} already has a scheduled appointment ({existing_conflict.appointment_id}) at {appt_time.strftime('%H:%M')} on {appt_date.strftime('%Y-%m-%d')}. Please pick another time slot.", 'danger')
            return redirect(url_for('appointments.create_appointment'))

        # Validation 6: Doctor daily capacity
        daily_count = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == appt_date,
            Appointment.status.notin_(['Cancelled', 'No Show'])
        ).count()

        if daily_count >= doctor.max_patient_capacity:
            flash(f"Dr. {doctor.name} has already reached the maximum patient capacity of {doctor.max_patient_capacity} for {appt_date.strftime('%Y-%m-%d')}.", 'warning')
            return redirect(url_for('appointments.create_appointment'))

        new_appt_id = generate_next_appointment_id()
        appt = Appointment(
            appointment_id=new_appt_id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            department_id=dept_id,
            appointment_date=appt_date,
            appointment_time=appt_time,
            status='Scheduled',
            reason=reason,
            notes=notes,
            is_demo=False
        )

        db.session.add(appt)
        db.session.commit()

        log_activity("CREATE_APPOINTMENT", "Appointments", f"Booked appointment {new_appt_id} for {patient.full_name} with Dr. {doctor.name}", record_id=new_appt_id)
        create_notification(
            title="New Appointment Scheduled",
            message=f"Appointment {new_appt_id} confirmed for {patient.full_name} with Dr. {doctor.name} on {appt_date.strftime('%b %d, %Y')} at {appt_time.strftime('%H:%M')}.",
            category="info",
            related_url="/appointments"
        )

        flash(f"Appointment {new_appt_id} scheduled successfully!", "success")
        return redirect(url_for('appointments.list_appointments'))

    departments = Department.query.filter_by(is_active=True).all()
    doctors = Doctor.query.filter_by(is_active=True).all()
    patients = Patient.query.order_by(Patient.full_name.asc()).limit(500).all()
    suggested_id = generate_next_appointment_id()

    # Pre-select patient if passed in query string
    pre_patient_id = request.args.get('patient_id', type=int)

    return render_template(
        'appointments/form.html',
        departments=departments,
        doctors=doctors,
        patients=patients,
        appointment=None,
        suggested_id=suggested_id,
        pre_patient_id=pre_patient_id
    )

@appointments_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    appt = Appointment.query.get_or_404(id)
    new_status = request.form.get('status')
    now = datetime.utcnow()

    valid_statuses = ['Scheduled', 'Confirmed', 'Waiting', 'In Consultation', 'Completed', 'Cancelled', 'No Show']
    if new_status not in valid_statuses:
        flash('Invalid status transition.', 'danger')
        return redirect(url_for('appointments.list_appointments'))

    old_status = appt.status
    appt.status = new_status

    # Synchronize Visit and Waiting Time timestamps automatically!
    visit = Visit.query.filter_by(appointment_id=appt.id).first()
    
    if new_status == 'Waiting':
        # Patient has arrived at the clinic!
        if not visit:
            visit = Visit(
                visit_id=f"VIS-{appt.appointment_id}",
                appointment_id=appt.id,
                patient_id=appt.patient_id,
                doctor_id=appt.doctor_id,
                department_id=appt.department_id,
                visit_date=appt.appointment_date,
                arrival_time=now,
                registration_time=now,
                status='Waiting',
                symptoms=appt.reason
            )
            db.session.add(visit)
        else:
            if not visit.arrival_time:
                visit.arrival_time = now
            visit.status = 'Waiting'

    elif new_status == 'In Consultation':
        # Consultation has started!
        if not visit:
            visit = Visit(
                visit_id=f"VIS-{appt.appointment_id}",
                appointment_id=appt.id,
                patient_id=appt.patient_id,
                doctor_id=appt.doctor_id,
                department_id=appt.department_id,
                visit_date=appt.appointment_date,
                arrival_time=now - timedelta(minutes=15),
                registration_time=now - timedelta(minutes=10),
                consultation_start_time=now,
                status='In Consultation',
                symptoms=appt.reason
            )
            db.session.add(visit)
        else:
            visit.consultation_start_time = now
            visit.status = 'In Consultation'
            visit.calculate_metrics()

    elif new_status == 'Completed':
        # Consultation has finished!
        if visit:
            if not visit.consultation_start_time:
                visit.consultation_start_time = now - timedelta(minutes=15)
            visit.consultation_end_time = now
            visit.status = 'Completed'
            visit.calculate_metrics()

    db.session.commit()
    log_activity("APPOINTMENT_STATUS", "Appointments", f"Updated {appt.appointment_id} status from {old_status} to {new_status}", record_id=appt.appointment_id)
    flash(f"Appointment {appt.appointment_id} updated to '{new_status}'.", "success")
    return redirect(request.referrer or url_for('appointments.list_appointments'))

@appointments_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(id):
    appt = Appointment.query.get_or_404(id)
    appt.status = 'Cancelled'
    db.session.commit()
    log_activity("CANCEL_APPOINTMENT", "Appointments", f"Cancelled appointment {appt.appointment_id}", record_id=appt.appointment_id)
    flash(f"Appointment {appt.appointment_id} has been cancelled.", "warning")
    return redirect(request.referrer or url_for('appointments.list_appointments'))
