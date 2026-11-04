from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from sqlalchemy import func
from app.extensions import db
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.models.bed import Bed, Admission
from app.models.notification import Notification, ActivityLog
from app.services.notification_service import check_and_trigger_alerts

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/analyst')
@dashboard_bp.route('/data-analyst')
@dashboard_bp.route('/analyst-panel')
@login_required
def analyst_redirect():
    from flask import redirect, url_for
    return redirect(url_for('analytics.index'))

@dashboard_bp.route('/')
@login_required
def index():
    # Trigger automated operational threshold check
    check_and_trigger_alerts()

    today = date.today()
    
    # 12 Core Dynamic KPI Cards directly from database queries
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.filter_by(is_active=True).count()
    available_doctors = Doctor.query.filter_by(is_active=True, availability_status='Available').count()
    
    total_appointments = Appointment.query.count()
    todays_appointments = Appointment.query.filter(Appointment.appointment_date == today).count()
    
    total_beds = Bed.query.count()
    occupied_beds = Bed.query.filter_by(occupancy_status='Occupied').count()
    available_beds = Bed.query.filter_by(occupancy_status='Available').count()
    bed_occupancy_pct = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

    # Average patient waiting time (only considering visits with valid calculated waiting time)
    avg_wait_result = db.session.query(func.avg(Visit.waiting_time_minutes)).filter(
        Visit.waiting_time_minutes.isnot(None),
        Visit.waiting_time_minutes > 0
    ).scalar()
    avg_waiting_time = round(float(avg_wait_result), 1) if avg_wait_result is not None else 0.0

    total_admissions = Admission.query.count()
    total_discharges = Admission.query.filter_by(status='Discharged').count()

    # Recent lists
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).limit(5).all()
    recent_admissions = Admission.query.order_by(Admission.id.desc()).limit(5).all()
    recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(6).all()
    departments = Department.query.filter_by(is_active=True).all()

    kpi_stats = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'available_doctors': available_doctors,
        'total_appointments': total_appointments,
        'todays_appointments': todays_appointments,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'bed_occupancy_pct': bed_occupancy_pct,
        'avg_waiting_time': avg_waiting_time,
        'total_admissions': total_admissions,
        'total_discharges': total_discharges
    }

    return render_template(
        'dashboard/index.html',
        kpi=kpi_stats,
        recent_patients=recent_patients,
        recent_appointments=recent_appointments,
        recent_admissions=recent_admissions,
        recent_activities=recent_activities,
        departments=departments
    )

@dashboard_bp.route('/api/dashboard/charts')
@login_required
def charts_api():
    """Dynamically computed data for Chart.js dashboard charts with optional department and date filters"""
    dept_id = request.args.get('department_id', type=int)
    days = request.args.get('days', default=30, type=int)
    
    start_date = date.today() - timedelta(days=days)

    # 1. Daily Patient Registrations Trend (past 14 days)
    daily_query = db.session.query(
        Patient.registration_date,
        func.count(Patient.id)
    ).filter(Patient.registration_date >= (date.today() - timedelta(days=14)))
    
    if dept_id:
        daily_query = daily_query.filter(Patient.assigned_department_id == dept_id)
        
    daily_records = daily_query.group_by(Patient.registration_date).order_by(Patient.registration_date.asc()).all()
    daily_labels = [r[0].strftime('%b %d') if r[0] else '' for r in daily_records]
    daily_values = [r[1] for r in daily_records]

    # 2. Department Patient Distribution
    dept_dist = db.session.query(
        Department.name,
        func.count(Patient.id)
    ).join(Patient, Patient.assigned_department_id == Department.id, isouter=True)\
     .group_by(Department.id, Department.name).all()

    dept_labels = [d[0] for d in dept_dist]
    dept_values = [d[1] for d in dept_dist]

    # 3. Doctor Availability Status
    doc_status = db.session.query(
        Doctor.availability_status,
        func.count(Doctor.id)
    ).group_by(Doctor.availability_status).all()
    
    doc_labels = [s[0] for s in doc_status]
    doc_values = [s[1] for s in doc_status]

    # 4. Bed Occupancy by Bed Type
    bed_types = db.session.query(
        Bed.bed_type,
        func.sum(db.case((Bed.occupancy_status == 'Occupied', 1), else_=0)),
        func.sum(db.case((Bed.occupancy_status == 'Available', 1), else_=0))
    ).group_by(Bed.bed_type).all()

    bed_type_labels = [b[0] for b in bed_types]
    bed_occupied_values = [int(b[1] or 0) for b in bed_types]
    bed_available_values = [int(b[2] or 0) for b in bed_types]

    # 5. Admission vs Discharge (Past 6 months or past weeks)
    adm_counts = db.session.query(
        func.date(Admission.admission_date),
        func.count(Admission.id)
    ).filter(Admission.admission_date >= start_date)\
     .group_by(func.date(Admission.admission_date)).order_by(func.date(Admission.admission_date)).limit(14).all()

    adm_dates = [str(a[0]) for a in adm_counts]
    adm_values = [a[1] for a in adm_counts]

    # 6. Average Waiting Time by Department
    dept_wait = db.session.query(
        Department.name,
        func.avg(Visit.waiting_time_minutes)
    ).join(Visit, Visit.department_id == Department.id)\
     .filter(Visit.waiting_time_minutes.isnot(None), Visit.waiting_time_minutes > 0)\
     .group_by(Department.name).all()

    dept_wait_labels = [w[0] for w in dept_wait]
    dept_wait_values = [round(float(w[1]), 1) for w in dept_wait]

    return jsonify({
        'daily_registrations': {
            'labels': daily_labels,
            'values': daily_values
        },
        'department_distribution': {
            'labels': dept_labels,
            'values': dept_values
        },
        'doctor_availability': {
            'labels': doc_labels,
            'values': doc_values
        },
        'bed_occupancy': {
            'labels': bed_type_labels,
            'occupied': bed_occupied_values,
            'available': bed_available_values
        },
        'admissions_trend': {
            'labels': adm_dates,
            'admissions': adm_values
        },
        'department_waiting_times': {
            'labels': dept_wait_labels,
            'values': dept_wait_values
        }
    })
