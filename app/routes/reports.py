from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import func
from app.extensions import db
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.models.bed import Bed, Admission
from app.models.ml import ModelRegistry
from app.ml.demand_forecaster import DemandForecaster
from app.services.export_service import export_to_csv, export_to_excel, export_to_pdf
from app.services.activity_logger import log_activity

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

REPORT_DEFINITIONS = [
    ('patients', 'Patient Registration Report'),
    ('doctors', 'Doctor Availability & Workload Report'),
    ('departments', 'Department Performance Report'),
    ('appointments', 'Appointment & Booking Report'),
    ('beds', 'Bed Occupancy & Utilization Report'),
    ('admissions', 'Admission & Discharge Summary Report'),
    ('waiting_time', 'Patient Waiting Time & Duration Report'),
    ('demand_forecast', 'Patient Demand Prediction Forecast Report'),
    ('ml_models', 'Machine Learning Models Evaluation Report')
]

@reports_bp.route('/')
@login_required
def index():
    report_type = request.args.get('type', 'patients')
    dept_id = request.args.get('department_id', type=int)
    days = request.args.get('days', default=30, type=int)
    export_format = request.args.get('export')

    start_date = date.today() - timedelta(days=days)

    headers = []
    rows = []
    report_title = "Hospital Report"

    # 1. Patient Registration Report
    if report_type == 'patients':
        report_title = "Patient Registration Report"
        headers = ["Patient ID", "Full Name", "Age", "Gender", "Phone", "Blood Group", "Registration Date", "Status"]
        query = Patient.query.filter(Patient.registration_date >= start_date)
        if dept_id:
            query = query.filter(Patient.assigned_department_id == dept_id)
        for p in query.order_by(Patient.id.desc()).limit(500).all():
            rows.append([
                p.patient_id, p.full_name, p.age, p.gender, p.phone,
                p.blood_group, p.registration_date.strftime('%Y-%m-%d') if p.registration_date else '', p.status
            ])

    # 2. Doctor Availability Report
    elif report_type == 'doctors':
        report_title = "Doctor Availability & Workload Report"
        headers = ["Doctor ID", "Name", "Department", "Specialization", "Availability Status", "Duty Hours", "Experience (Yrs)", "Max Capacity"]
        query = Doctor.query
        if dept_id:
            query = query.filter(Doctor.department_id == dept_id)
        for d in query.order_by(Doctor.name.asc()).all():
            rows.append([
                d.doctor_id, f"Dr. {d.name}", d.department.name if d.department else '',
                d.specialization, d.availability_status,
                f"{d.duty_start_time.strftime('%H:%M')} - {d.duty_end_time.strftime('%H:%M')}",
                d.experience_years, d.max_patient_capacity
            ])

    # 3. Department Performance Report
    elif report_type == 'departments':
        report_title = "Department Performance Report"
        headers = ["Department Code", "Department Name", "Doctors", "Beds Count", "Active Patients", "Today's Appointments", "Avg Waiting Time (m)"]
        for dept in Department.query.all():
            today_appts = Appointment.query.filter(Appointment.department_id == dept.id, Appointment.appointment_date == date.today()).count()
            avg_w = db.session.query(func.avg(Visit.waiting_time_minutes)).filter(Visit.department_id == dept.id, Visit.waiting_time_minutes.isnot(None)).scalar()
            rows.append([
                dept.code, dept.name, len(dept.doctors), len(dept.beds), len(dept.patients),
                today_appts, round(float(avg_w), 1) if avg_w else 0.0
            ])

    # 4. Appointment Report
    elif report_type == 'appointments':
        report_title = "Appointment & Booking Report"
        headers = ["Appt ID", "Patient Name", "Doctor", "Department", "Date", "Time", "Status", "Reason"]
        query = Appointment.query.filter(Appointment.appointment_date >= start_date)
        if dept_id:
            query = query.filter(Appointment.department_id == dept_id)
        for a in query.order_by(Appointment.appointment_date.desc()).limit(500).all():
            rows.append([
                a.appointment_id, a.patient.full_name if a.patient else 'Unknown',
                f"Dr. {a.doctor.name}" if a.doctor else 'Unknown',
                a.department.name if a.department else '',
                a.appointment_date.strftime('%Y-%m-%d'), a.appointment_time.strftime('%H:%M'),
                a.status, a.reason or ''
            ])

    # 5. Bed Occupancy Report
    elif report_type == 'beds':
        report_title = "Bed Occupancy & Utilization Report"
        headers = ["Bed ID", "Bed Number", "Department", "Ward", "Bed Type", "Status", "Assigned Patient"]
        query = Bed.query
        if dept_id:
            query = query.filter(Bed.department_id == dept_id)
        for b in query.order_by(Bed.department_id.asc()).all():
            rows.append([
                b.bed_id, b.bed_number, b.department.name if b.department else '',
                b.ward, b.bed_type, b.occupancy_status,
                b.current_patient.full_name if b.current_patient else 'None'
            ])

    # 6. Admission and Discharge Report
    elif report_type == 'admissions':
        report_title = "Admission & Discharge Summary Report"
        headers = ["Admission ID", "Patient Name", "Department", "Doctor", "Bed", "Admission Date", "Discharge Date", "Status", "Reason"]
        query = Admission.query.filter(Admission.admission_date >= start_date)
        if dept_id:
            query = query.filter(Admission.department_id == dept_id)
        for adm in query.order_by(Admission.admission_date.desc()).limit(500).all():
            rows.append([
                adm.admission_id, adm.patient.full_name if adm.patient else '',
                adm.department.name if adm.department else '',
                f"Dr. {adm.doctor.name}" if adm.doctor else '',
                adm.bed.bed_id if adm.bed else '',
                adm.admission_date.strftime('%Y-%m-%d %H:%M'),
                adm.discharge_date.strftime('%Y-%m-%d %H:%M') if adm.discharge_date else 'Active Inpatient',
                adm.status, adm.admission_reason
            ])

    # 7. Waiting Time Report
    elif report_type == 'waiting_time':
        report_title = "Patient Waiting Time & Duration Report"
        headers = ["Visit ID", "Patient Name", "Doctor", "Department", "Visit Date", "Arrival Time", "Consult Start", "Waiting Time (min)", "Duration (min)"]
        query = Visit.query.filter(Visit.visit_date >= start_date, Visit.waiting_time_minutes.isnot(None))
        if dept_id:
            query = query.filter(Visit.department_id == dept_id)
        for v in query.order_by(Visit.id.desc()).limit(500).all():
            rows.append([
                v.visit_id, v.patient.full_name if v.patient else '',
                f"Dr. {v.doctor.name}" if v.doctor else '',
                v.department.name if v.department else '',
                v.visit_date.strftime('%Y-%m-%d'),
                v.arrival_time.strftime('%H:%M') if v.arrival_time else '',
                v.consultation_start_time.strftime('%H:%M') if v.consultation_start_time else '',
                v.waiting_time_minutes or 0,
                v.consultation_duration_minutes or 0
            ])

    # 8. Patient Demand Prediction Report
    elif report_type == 'demand_forecast':
        report_title = "Patient Demand Prediction Forecast Report"
        headers = ["Forecast Date", "Day of Week", "Predicted Patient Volume", "Lower Confidence (95%)", "Upper Confidence (95%)"]
        forecaster = DemandForecaster()
        data = forecaster.forecast_next_days(days=14)
        for item in data.get('forecasts', []):
            rows.append([
                item['date'], item['day_name'], item['predicted_patients'],
                item['lower_bound'], item['upper_bound']
            ])

    # 9. ML Models Evaluation Report
    elif report_type == 'ml_models':
        report_title = "Machine Learning Models Evaluation Report"
        headers = ["Model Target", "Algorithm Name", "Version", "MAE", "RMSE", "R² Score", "Active Status", "Trained At"]
        for m in ModelRegistry.query.order_by(ModelRegistry.model_name.asc(), ModelRegistry.rmse.asc()).all():
            rows.append([
                m.model_name.replace('_', ' ').title(), m.algorithm_name, m.version,
                round(m.mae, 3), round(m.rmse, 3), round(m.r2_score, 4),
                "YES (Selected)" if m.is_active else "No",
                m.trained_at.strftime('%Y-%m-%d %H:%M')
            ])

    # Handle file download requests
    if export_format:
        filename_prefix = f"hospital_report_{report_type}_{datetime.utcnow().strftime('%Y%m%d')}"
        log_activity("EXPORT_REPORT", "Reports", f"Exported {report_title} in {export_format.upper()} format")

        if export_format == 'csv':
            csv_bytes = export_to_csv(headers, rows)
            return Response(
                csv_bytes,
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={filename_prefix}.csv"}
            )
        elif export_format == 'excel':
            excel_bytes = export_to_excel(report_type[:30], headers, rows)
            return Response(
                excel_bytes,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-disposition": f"attachment; filename={filename_prefix}.xlsx"}
            )
        elif export_format == 'pdf':
            pdf_bytes = export_to_pdf(report_title, headers, rows, orientation='landscape')
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={"Content-disposition": f"attachment; filename={filename_prefix}.pdf"}
            )

    departments = Department.query.filter_by(is_active=True).all()
    return render_template(
        'reports/index.html',
        report_definitions=REPORT_DEFINITIONS,
        active_type=report_type,
        report_title=report_title,
        headers=headers,
        rows=rows,
        departments=departments,
        dept_id=dept_id,
        days=days
    )
