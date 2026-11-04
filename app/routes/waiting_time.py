from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sqlalchemy import func, or_
from app.extensions import db
from app.models.visit import Visit
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.settings import HospitalSetting
from app.services.activity_logger import log_activity

waiting_time_bp = Blueprint('waiting_time', __name__, url_prefix='/waiting-time')

@waiting_time_bp.route('/')
@login_required
def index():
    dept_id = request.args.get('department_id', type=int)
    doc_id = request.args.get('doctor_id', type=int)
    date_str = request.args.get('date', '').strip()
    status_tab = request.args.get('tab', 'completed')  # 'completed' or 'incomplete' or 'active'

    query = Visit.query

    if dept_id:
        query = query.filter(Visit.department_id == dept_id)
    if doc_id:
        query = query.filter(Visit.doctor_id == doc_id)
    if date_str:
        try:
            d = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(Visit.visit_date == d)
        except ValueError:
            pass

    # Separate complete visits from incomplete visits
    if status_tab == 'incomplete':
        query = query.filter(
            or_(
                Visit.arrival_time.is_(None),
                Visit.consultation_start_time.is_(None)
            )
        )
    elif status_tab == 'active':
        query = query.filter(Visit.status.in_(['Waiting', 'In Consultation']))
    else:
        # Completed / verified records with actual calculated waiting times
        query = query.filter(
            Visit.waiting_time_minutes.isnot(None),
            Visit.waiting_time_minutes > 0
        )

    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Visit.id.desc()).paginate(page=page, per_page=15, error_out=False)
    visits = pagination.items

    # Core statistical aggregates (only over complete records)
    valid_query = db.session.query(Visit).filter(
        Visit.waiting_time_minutes.isnot(None),
        Visit.waiting_time_minutes > 0
    )
    if dept_id:
        valid_query = valid_query.filter(Visit.department_id == dept_id)
    if doc_id:
        valid_query = valid_query.filter(Visit.doctor_id == doc_id)

    avg_wait = valid_query.with_entities(func.avg(Visit.waiting_time_minutes)).scalar()
    longest_wait = valid_query.with_entities(func.max(Visit.waiting_time_minutes)).scalar()
    shortest_wait = valid_query.with_entities(func.min(Visit.waiting_time_minutes)).scalar()
    avg_duration = valid_query.with_entities(func.avg(Visit.consultation_duration_minutes)).scalar()

    # Incomplete records count
    incomplete_count = Visit.query.filter(
        or_(
            Visit.arrival_time.is_(None),
            Visit.consultation_start_time.is_(None)
        )
    ).count()

    active_waiting_count = Visit.query.filter_by(status='Waiting').count()
    active_in_consult_count = Visit.query.filter_by(status='In Consultation').count()

    # Department-wise breakdown with alert for exceeding threshold
    settings = HospitalSetting.get_settings()
    threshold = settings.waiting_time_alert_threshold

    dept_stats = db.session.query(
        Department.name,
        func.avg(Visit.waiting_time_minutes),
        func.count(Visit.id)
    ).join(Visit, Visit.department_id == Department.id)\
     .filter(Visit.waiting_time_minutes.isnot(None), Visit.waiting_time_minutes > 0)\
     .group_by(Department.name).all()

    departments_summary = []
    for name, avg_w, count in dept_stats:
        avg_val = round(float(avg_w), 1) if avg_w else 0.0
        departments_summary.append({
            'name': name,
            'avg_wait': avg_val,
            'visits_count': count,
            'is_high': avg_val >= threshold
        })

    departments = Department.query.filter_by(is_active=True).all()
    doctors = Doctor.query.filter_by(is_active=True).all()

    metrics = {
        'avg_wait': round(float(avg_wait), 1) if avg_wait else 0.0,
        'longest_wait': round(float(longest_wait), 1) if longest_wait else 0.0,
        'shortest_wait': round(float(shortest_wait), 1) if shortest_wait else 0.0,
        'avg_duration': round(float(avg_duration), 1) if avg_duration else 0.0,
        'incomplete_count': incomplete_count,
        'active_waiting': active_waiting_count,
        'active_in_consult': active_in_consult_count,
        'threshold': threshold
    }

    return render_template(
        'waiting_time/index.html',
        visits=visits,
        pagination=pagination,
        metrics=metrics,
        departments_summary=departments_summary,
        departments=departments,
        doctors=doctors,
        dept_id=dept_id,
        doc_id=doc_id,
        date_str=date_str,
        status_tab=status_tab
    )

@waiting_time_bp.route('/api/charts')
@login_required
def charts_data():
    """Dynamically calculated waiting time metrics for visual charts"""
    dept_id = request.args.get('department_id', type=int)

    # 1. Waiting Time by Hour of Day
    visits = Visit.query.filter(
        Visit.waiting_time_minutes.isnot(None),
        Visit.arrival_time.isnot(None)
    )
    if dept_id:
        visits = visits.filter(Visit.department_id == dept_id)
    
    hourly_data = {h: [] for h in range(8, 20)}
    for v in visits.limit(1000).all():
        if v.arrival_time:
            hour = v.arrival_time.hour
            if hour in hourly_data:
                hourly_data[hour].append(v.waiting_time_minutes)

    hourly_labels = [f"{h}:00" for h in range(8, 20)]
    hourly_averages = [
        round(sum(hourly_data[h]) / len(hourly_data[h]), 1) if hourly_data[h] else 0.0
        for h in range(8, 20)
    ]

    # 2. Doctor consultation duration comparison
    doc_durations = db.session.query(
        Doctor.name,
        func.avg(Visit.consultation_duration_minutes)
    ).join(Visit, Visit.doctor_id == Doctor.id)\
     .filter(Visit.consultation_duration_minutes.isnot(None))\
     .group_by(Doctor.id, Doctor.name).limit(10).all()

    doc_names = [f"Dr. {d[0]}" for d in doc_durations]
    doc_times = [round(float(d[1]), 1) for d in doc_durations]

    return jsonify({
        'hourly': {
            'labels': hourly_labels,
            'averages': hourly_averages
        },
        'doctor_durations': {
            'labels': doc_names,
            'durations': doc_times
        }
    })

@waiting_time_bp.route('/record-timestamp/<int:id>', methods=['POST'])
@login_required
def update_timestamp(id):
    """Manually update or complete a visit's timestamps"""
    visit = Visit.query.get_or_404(id)
    action = request.form.get('action')
    now = datetime.utcnow()

    if action == 'mark_arrival':
        visit.arrival_time = now
        visit.status = 'Waiting'
    elif action == 'start_consultation':
        if not visit.arrival_time:
            visit.arrival_time = now - timedelta(minutes=10)
        visit.consultation_start_time = now
        visit.status = 'In Consultation'
        visit.calculate_metrics()
    elif action == 'end_consultation':
        if not visit.consultation_start_time:
            visit.consultation_start_time = now - timedelta(minutes=15)
        visit.consultation_end_time = now
        visit.status = 'Completed'
        visit.calculate_metrics()

    db.session.commit()
    log_activity("UPDATE_VISIT_TIMESTAMP", "Waiting Time", f"Updated timestamps for visit {visit.visit_id}: {action}", record_id=visit.visit_id)
    flash(f"Timestamps updated for visit {visit.visit_id}.", "success")
    return redirect(request.referrer or url_for('waiting_time.index'))
