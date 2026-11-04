from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sqlalchemy import or_
from app.extensions import db
from app.models.patient import Patient
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.models.bed import Admission
from app.services.activity_logger import log_activity
from app.services.auth_decorators import permission_required

patients_bp = Blueprint('patients', __name__, url_prefix='/patients')

def generate_next_patient_id():
    year_month = datetime.utcnow().strftime('%Y%m')
    prefix = f"PAT-{year_month}-"
    last_patient = Patient.query.filter(Patient.patient_id.like(f"{prefix}%")).order_by(Patient.id.desc()).first()
    if last_patient:
        try:
            seq = int(last_patient.patient_id.split('-')[-1]) + 1
        except ValueError:
            seq = Patient.query.count() + 1
    else:
        seq = Patient.query.count() + 1
    return f"{prefix}{seq:04d}"

@patients_bp.route('/')
@login_required
def list_patients():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    gender_filter = request.args.get('gender', '').strip()
    dept_filter = request.args.get('department_id', type=int)

    query = Patient.query

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Patient.full_name.ilike(search_fmt),
                Patient.patient_id.ilike(search_fmt),
                Patient.phone.ilike(search_fmt)
            )
        )

    if status_filter:
        query = query.filter(Patient.status == status_filter)

    if gender_filter:
        query = query.filter(Patient.gender == gender_filter)

    if dept_filter:
        query = query.filter(Patient.assigned_department_id == dept_filter)

    pagination = query.order_by(Patient.id.desc()).paginate(page=page, per_page=15, error_out=False)
    departments = Department.query.filter_by(is_active=True).all()

    return render_template(
        'patients/list.html',
        pagination=pagination,
        patients=pagination.items,
        search=search,
        status_filter=status_filter,
        gender_filter=gender_filter,
        dept_filter=dept_filter,
        departments=departments
    )

@patients_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_patient():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        age = request.form.get('age', type=int)
        dob_str = request.form.get('dob')
        gender = request.form.get('gender', 'Male')
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        blood_group = request.form.get('blood_group', 'O+')
        emergency_contact = request.form.get('emergency_contact', '').strip()
        dept_id = request.form.get('assigned_department_id', type=int)

        if not full_name or not age or not phone:
            flash('Please provide Full Name, Age, and Contact Phone Number.', 'danger')
            return redirect(url_for('patients.create_patient'))

        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        new_pat_id = generate_next_patient_id()

        patient = Patient(
            patient_id=new_pat_id,
            full_name=full_name,
            age=age,
            dob=dob,
            gender=gender,
            phone=phone,
            email=email if email else None,
            address=address,
            blood_group=blood_group,
            emergency_contact=emergency_contact,
            registration_date=date.today(),
            assigned_department_id=dept_id,
            status='Outpatient',
            is_demo=False
        )

        db.session.add(patient)
        db.session.commit()

        log_activity("CREATE_PATIENT", "Patients", f"Registered new patient {new_pat_id}: {full_name}", record_id=new_pat_id)
        flash(f"Patient {full_name} registered successfully with ID {new_pat_id}!", "success")
        return redirect(url_for('patients.view_patient', id=patient.id))

    departments = Department.query.filter_by(is_active=True).all()
    suggested_id = generate_next_patient_id()
    return render_template('patients/form.html', departments=departments, patient=None, suggested_id=suggested_id)

@patients_bp.route('/<int:id>')
@login_required
def view_patient(id):
    patient = Patient.query.get_or_404(id)
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.appointment_date.desc()).all()
    visits = Visit.query.filter_by(patient_id=patient.id).order_by(Visit.visit_date.desc()).all()
    admissions = Admission.query.filter_by(patient_id=patient.id).order_by(Admission.admission_date.desc()).all()

    return render_template(
        'patients/profile.html',
        patient=patient,
        appointments=appointments,
        visits=visits,
        admissions=admissions
    )

@patients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)

    if request.method == 'POST':
        patient.full_name = request.form.get('full_name', '').strip()
        patient.age = request.form.get('age', type=int)
        dob_str = request.form.get('dob')
        patient.dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else patient.dob
        patient.gender = request.form.get('gender', patient.gender)
        patient.phone = request.form.get('phone', '').strip()
        patient.email = request.form.get('email', '').strip()
        patient.address = request.form.get('address', '').strip()
        patient.blood_group = request.form.get('blood_group', patient.blood_group)
        patient.emergency_contact = request.form.get('emergency_contact', '').strip()
        patient.assigned_department_id = request.form.get('assigned_department_id', type=int)

        db.session.commit()
        log_activity("EDIT_PATIENT", "Patients", f"Updated details for patient {patient.patient_id}", record_id=patient.patient_id)
        flash(f"Patient {patient.full_name} details updated successfully.", "success")
        return redirect(url_for('patients.view_patient', id=patient.id))

    departments = Department.query.filter_by(is_active=True).all()
    return render_template('patients/form.html', departments=departments, patient=patient, suggested_id=patient.patient_id)

@patients_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    
    # Check if patient is currently admitted
    if patient.status == 'Admitted':
        flash('Cannot delete patient while currently admitted to an active hospital bed. Please process discharge first.', 'danger')
        return redirect(url_for('patients.view_patient', id=id))

    pat_name = patient.full_name
    pat_code = patient.patient_id

    db.session.delete(patient)
    db.session.commit()

    log_activity("DELETE_PATIENT", "Patients", f"Archived/deleted record for patient {pat_code}: {pat_name}", record_id=pat_code)
    flash(f"Patient record for {pat_name} ({pat_code}) deleted.", "info")
    return redirect(url_for('patients.list_patients'))
