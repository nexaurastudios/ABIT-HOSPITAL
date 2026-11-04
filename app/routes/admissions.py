from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.bed import Bed, Admission
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.services.activity_logger import log_activity
from app.services.notification_service import create_notification, check_and_trigger_alerts

admissions_bp = Blueprint('admissions', __name__, url_prefix='/admissions')

def generate_next_admission_id():
    year_month = datetime.utcnow().strftime('%Y%m')
    prefix = f"ADM-{year_month}-"
    last_adm = Admission.query.filter(Admission.admission_id.like(f"{prefix}%")).order_by(Admission.id.desc()).first()
    if last_adm:
        try:
            seq = int(last_adm.admission_id.split('-')[-1]) + 1
        except ValueError:
            seq = Admission.query.count() + 1
    else:
        seq = Admission.query.count() + 1
    return f"{prefix}{seq:04d}"

@admissions_bp.route('/')
@login_required
def list_admissions():
    status_filter = request.args.get('status', 'Active')
    dept_filter = request.args.get('department_id', type=int)

    query = Admission.query
    if status_filter:
        query = query.filter(Admission.status == status_filter)
    if dept_filter:
        query = query.filter(Admission.department_id == dept_filter)

    admissions = query.order_by(Admission.admission_date.desc()).all()
    departments = Department.query.filter_by(is_active=True).all()

    active_count = Admission.query.filter_by(status='Active').count()
    discharged_count = Admission.query.filter_by(status='Discharged').count()

    return render_template(
        'admissions/list.html',
        admissions=admissions,
        departments=departments,
        status_filter=status_filter,
        dept_filter=dept_filter,
        active_count=active_count,
        discharged_count=discharged_count
    )

@admissions_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_admission():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id', type=int)
        dept_id = request.form.get('department_id', type=int)
        doctor_id = request.form.get('doctor_id', type=int)
        bed_id = request.form.get('bed_id', type=int)
        adm_reason = request.form.get('admission_reason', '').strip()
        diagnosis = request.form.get('diagnosis', '').strip()

        if not patient_id or not dept_id or not doctor_id or not bed_id or not adm_reason:
            flash('All fields (Patient, Department, Doctor, Bed, and Reason) are required.', 'danger')
            return redirect(url_for('admissions.create_admission'))

        patient = Patient.query.get(patient_id)
        if not patient:
            flash('Selected patient record does not exist.', 'danger')
            return redirect(url_for('admissions.create_admission'))

        # Validation: Check if patient already has an active admission
        existing_active = Admission.query.filter_by(patient_id=patient.id, status='Active').first()
        if existing_active:
            flash(f"Patient {patient.full_name} is already admitted under admission {existing_active.admission_id} (Bed {existing_active.bed.bed_id}). Cannot create duplicate active admission.", 'danger')
            return redirect(url_for('admissions.create_admission'))

        # ATOMIC TRANSACTION: Check bed occupancy with row lock / transaction check
        try:
            # Query bed with with_for_update if supported or strict check
            bed = Bed.query.filter_by(id=bed_id).with_for_update().first()
            if not bed or bed.occupancy_status != 'Available':
                db.session.rollback()
                flash(f"Selected bed is no longer available. It may have just been allocated to another patient. Please choose another bed.", 'danger')
                return redirect(url_for('admissions.create_admission'))

            new_adm_id = generate_next_admission_id()
            now = datetime.utcnow()

            admission = Admission(
                admission_id=new_adm_id,
                patient_id=patient.id,
                department_id=dept_id,
                doctor_id=doctor_id,
                bed_id=bed.id,
                admission_date=now,
                admission_reason=adm_reason,
                diagnosis=diagnosis,
                status='Active',
                is_demo=False
            )
            db.session.add(admission)
            db.session.flush()

            # Atomically update bed status
            bed.occupancy_status = 'Occupied'
            bed.current_patient_id = patient.id
            bed.current_admission_id = admission.id

            # Update patient status
            patient.status = 'Admitted'
            patient.assigned_department_id = dept_id

            db.session.commit()

            log_activity("PATIENT_ADMISSION", "Admissions", f"Admitted {patient.full_name} ({patient.patient_id}) to {bed.bed_id} under Dr. {admission.doctor.name}", record_id=new_adm_id)
            create_notification(
                title="New Inpatient Admission",
                message=f"Patient {patient.full_name} admitted to {bed.ward} ({bed.bed_id}) for {adm_reason}.",
                category="info",
                related_url="/admissions"
            )
            check_and_trigger_alerts()

            flash(f"Patient {patient.full_name} admitted successfully to {bed.bed_id} (Admission ID: {new_adm_id})!", "success")
            return redirect(url_for('admissions.list_admissions'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error processing admission transaction: {str(e)}", "danger")
            return redirect(url_for('admissions.create_admission'))

    # GET: Populate form options
    departments = Department.query.filter_by(is_active=True).all()
    doctors = Doctor.query.filter_by(is_active=True).all()
    # Only patients not currently admitted
    patients = Patient.query.filter(Patient.status != 'Admitted').order_by(Patient.full_name.asc()).limit(300).all()
    available_beds = Bed.query.filter_by(occupancy_status='Available').all()
    suggested_id = generate_next_admission_id()

    pre_patient_id = request.args.get('patient_id', type=int)

    return render_template(
        'admissions/new_admission.html',
        departments=departments,
        doctors=doctors,
        patients=patients,
        available_beds=available_beds,
        suggested_id=suggested_id,
        pre_patient_id=pre_patient_id
    )

@admissions_bp.route('/<int:id>/discharge', methods=['POST'])
@login_required
def discharge_patient(id):
    admission = Admission.query.get_or_404(id)

    if admission.status != 'Active':
        flash('This admission has already been discharged.', 'warning')
        return redirect(url_for('admissions.list_admissions'))

    discharge_condition = request.form.get('discharge_condition', 'Recovered')
    discharge_notes = request.form.get('discharge_notes', '').strip()

    try:
        now = datetime.utcnow()
        admission.status = 'Discharged'
        admission.discharge_date = now
        admission.discharge_condition = discharge_condition
        admission.discharge_notes = discharge_notes

        # Atomically release the bed
        bed = Bed.query.get(admission.bed_id)
        if bed:
            bed.occupancy_status = 'Available'
            bed.current_patient_id = None
            bed.current_admission_id = None

        # Update patient status
        patient = Patient.query.get(admission.patient_id)
        if patient:
            patient.status = 'Discharged'

        db.session.commit()

        log_activity(
            "PATIENT_DISCHARGE",
            "Admissions",
            f"Discharged patient {patient.full_name if patient else ''} from {bed.bed_id if bed else ''}. Condition: {discharge_condition}",
            record_id=admission.admission_id
        )
        create_notification(
            title="Patient Discharged",
            message=f"Admission {admission.admission_id} closed. Bed {bed.bed_id if bed else ''} is now available.",
            category="success",
            related_url="/beds"
        )

        flash(f"Patient discharged successfully. Bed {bed.bed_id if bed else ''} has been marked Available.", "success")
        return redirect(url_for('admissions.list_admissions'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error executing discharge transaction: {str(e)}", "danger")
        return redirect(url_for('admissions.list_admissions'))
