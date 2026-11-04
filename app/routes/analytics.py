import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from sqlalchemy import func
from app.extensions import db
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.models.bed import Bed, Admission
from app.models.resource import Resource
from app.models.ml import ModelRegistry
from app.ml.demand_forecaster import DemandForecaster
from app.ml.waiting_time_predictor import WaitingTimePredictor

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/panel')
@analytics_bp.route('/')
@login_required
def index():
    active_tab = request.args.get('tab', 'patients')
    days = request.args.get('days', 30, type=int)
    start_date = date.today() - timedelta(days=days)

    # 1. Patient Analytics with Pandas
    patients_df = pd.DataFrame([
        {'id': p.id, 'age': p.age, 'gender': p.gender, 'reg_date': p.registration_date, 'blood_group': p.blood_group, 'status': p.status}
        for p in Patient.query.all()
    ])

    patient_stats = {}
    if not patients_df.empty:
        # Age groups
        bins = [0, 18, 35, 50, 65, 120]
        labels = ['0-17 (Pediatric)', '18-35 (Young Adult)', '36-50 (Adult)', '51-65 (Middle Aged)', '65+ (Senior)']
        patients_df['age_group'] = pd.cut(patients_df['age'], bins=bins, labels=labels, right=False)
        age_dist = patients_df['age_group'].value_counts().to_dict()

        gender_dist = patients_df['gender'].value_counts().to_dict()
        blood_dist = patients_df['blood_group'].value_counts().to_dict()

        # Returning vs New patients (patients with > 1 appointment or visit)
        visit_counts = db.session.query(Visit.patient_id, func.count(Visit.id)).group_by(Visit.patient_id).all()
        returning_pat_ids = set(p_id for p_id, count in visit_counts if count > 1)
        total_p = len(patients_df)
        returning_count = len(returning_pat_ids)
        new_count = max(0, total_p - returning_count)

        patient_stats = {
            'total': total_p,
            'new_count': new_count,
            'returning_count': returning_count,
            'returning_pct': round((returning_count / total_p * 100), 1) if total_p > 0 else 0,
            'age_distribution': age_dist,
            'gender_distribution': gender_dist,
            'blood_distribution': blood_dist,
            'avg_age': round(patients_df['age'].mean(), 1)
        }

    # 2. Department Analytics
    depts = Department.query.all()
    dept_analytics = []
    for d in depts:
        doc_count = len(d.doctors)
        patient_count = len(d.patients)
        bed_count = len(d.beds)
        occupied_beds = sum(1 for b in d.beds if b.occupancy_status == 'Occupied')
        
        visits_for_dept = Visit.query.filter_by(department_id=d.id).all()
        completed_visits = sum(1 for v in visits_for_dept if v.status == 'Completed')
        
        avg_wait = np.mean([v.waiting_time_minutes for v in visits_for_dept if v.waiting_time_minutes]) if visits_for_dept else 0.0

        dept_analytics.append({
            'name': d.name,
            'code': d.code,
            'doctors': doc_count,
            'patients': patient_count,
            'beds': bed_count,
            'bed_occupancy': round((occupied_beds / bed_count * 100), 1) if bed_count > 0 else 0,
            'throughput': completed_visits,
            'avg_wait_minutes': round(float(avg_wait), 1) if not np.isnan(avg_wait) else 0.0
        })

    # 3. Doctor Analytics with Pandas
    doctors = Doctor.query.all()
    doc_analytics = []
    for doc in doctors:
        v_list = Visit.query.filter_by(doctor_id=doc.id).all()
        completed_c = sum(1 for v in v_list if v.status == 'Completed')
        durations = [v.consultation_duration_minutes for v in v_list if v.consultation_duration_minutes]
        avg_dur = round(float(np.mean(durations)), 1) if durations else 15.0

        doc_analytics.append({
            'id': doc.doctor_id,
            'name': doc.name,
            'department': doc.department.name if doc.department else 'N/A',
            'specialization': doc.specialization,
            'status': doc.availability_status,
            'patients_handled': completed_c,
            'avg_duration': avg_dur,
            'experience': doc.experience_years
        })

    # 4. Hospital Resource Analytics
    resources = Resource.query.all()
    resource_data = [r.to_dict() for r in resources]

    # Bed occupancy breakdown
    total_beds = Bed.query.count()
    bed_types_summary = db.session.query(
        Bed.bed_type,
        func.count(Bed.id),
        func.sum(db.case((Bed.occupancy_status == 'Occupied', 1), else_=0))
    ).group_by(Bed.bed_type).all()

    bed_type_stats = []
    for b_type, total, occ in bed_types_summary:
        occ_int = int(occ or 0)
        bed_type_stats.append({
            'type': b_type,
            'total': total,
            'occupied': occ_int,
            'available': total - occ_int,
            'rate': round((occ_int / total * 100), 1) if total > 0 else 0
        })

    # 5. Waiting Time Analytics
    visits_with_wait = Visit.query.filter(
        Visit.waiting_time_minutes.isnot(None),
        Visit.waiting_time_minutes > 0
    ).all()

    wait_stats = {}
    if visits_with_wait:
        wait_times = [v.waiting_time_minutes for v in visits_with_wait]
        wait_stats = {
            'mean': round(float(np.mean(wait_times)), 1),
            'median': round(float(np.median(wait_times)), 1),
            'std_dev': round(float(np.std(wait_times)), 1),
            'percentile_90': round(float(np.percentile(wait_times, 90)), 1),
            'min': round(float(np.min(wait_times)), 1),
            'max': round(float(np.max(wait_times)), 1)
        }

    return render_template(
        'analytics/index.html',
        active_tab=active_tab,
        patient_stats=patient_stats,
        dept_analytics=dept_analytics,
        doc_analytics=doc_analytics,
        resource_data=resource_data,
        bed_type_stats=bed_type_stats,
        wait_stats=wait_stats,
        days=days
    )
